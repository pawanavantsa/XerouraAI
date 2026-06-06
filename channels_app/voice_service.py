"""Twilio Voice + optional ElevenLabs TTS. STT via Twilio <Gather input="speech">."""

from __future__ import annotations

import html
import logging
import uuid
from pathlib import Path

import requests
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

logger = logging.getLogger(__name__)


def escape_twiml_text(text: str) -> str:
    """Escape text for Twilio <Say> body (XML)."""
    return html.escape((text or "").strip(), quote=False)


def escape_twiml_attr(text: str) -> str:
    """Escape text for XML attribute values (e.g. Twilio action URLs)."""
    return html.escape(text or "", quote=True)


def public_base_url(request: HttpRequest | None = None) -> str:
    base = getattr(settings, "PUBLIC_BASE_URL", "") or ""
    base = base.strip().rstrip("/")
    if base:
        return base
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    return ""


def absolute_url(
    request: HttpRequest | None,
    viewname: str,
    **kwargs,
) -> str:
    base = public_base_url(request)
    if not base:
        logger.error(
            "Voice URL build failed: set PUBLIC_BASE_URL or pass HttpRequest "
            "(view %s)",
            viewname,
        )
        base = "https://configure-public-base-url.invalid"
    path = reverse(viewname, kwargs=kwargs)
    if base.endswith("/") and path.startswith("/"):
        return base[:-1] + path
    if not base.endswith("/") and not path.startswith("/"):
        return f"{base}/{path}"
    return base + path


def validate_twilio_signature(request: HttpRequest) -> bool:
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "") or ""
    if not token or settings.DEBUG:
        return True
    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        logger.warning("twilio not installed — skipping signature validation")
        return True

    validator = RequestValidator(token)
    proto = request.META.get("HTTP_X_FORWARDED_PROTO", request.scheme)
    host = request.META.get("HTTP_X_FORWARDED_HOST", request.get_host())
    url = f"{proto}://{host}{request.get_full_path()}"
    sig = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
    params = request.POST.dict()
    return bool(validator.validate(url, params, sig))


def synthesize_elevenlabs_mp3(text: str) -> bytes | None:
    api_key = getattr(settings, "ELEVENLABS_API_KEY", "") or ""
    if not api_key or not text.strip():
        return None
    voice_id = getattr(settings, "ELEVENLABS_VOICE_ID", "") or "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    try:
        resp = requests.post(
            url,
            headers={
                "xi-api-key": api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json={
                "text": text[:2500],
                "model_id": getattr(
                    settings, "ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5"
                ),
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        logger.exception("ElevenLabs request failed: %s", exc)
        return None
    if resp.status_code != 200:
        logger.error(
            "ElevenLabs HTTP %s: %s", resp.status_code, resp.text[:500]
        )
        return None
    return resp.content


def write_tts_file(mp3: bytes) -> uuid.UUID:
    root = Path(settings.MEDIA_ROOT) / "voice_tts"
    root.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    path = root / f"{file_id}.mp3"
    path.write_bytes(mp3)
    return file_id


def twiml_document(inner: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{inner}</Response>'


def twiml_gather_loop(
    request: HttpRequest | None,
    prompt_say: str | None = None,
    play_url: str | None = None,
) -> str:
    """After AI audio, gather next user utterance and POST to gather URL."""
    gather_action = absolute_url(
        request, "channels_app:voice-gather"
    )
    ga = escape_twiml_attr(gather_action)
    inner = ""
    if play_url:
        inner += f'<Play>{escape_twiml_text(play_url)}</Play>'
    elif prompt_say:
        inner += (
            f'<Say voice="Polly.Joanna">{escape_twiml_text(prompt_say)}</Say>'
        )
    inner += (
        f'<Gather input="speech" action="{ga}" '
        'method="POST" speechTimeout="auto" language="en-US" '
        'speechModel="phone_call" enhanced="true">'
        '<Say voice="Polly.Joanna">Please go ahead.</Say>'
        "</Gather>"
        f'<Redirect method="POST">{escape_twiml_text(gather_action)}</Redirect>'
    )
    return twiml_document(inner)


def twiml_welcome_then_gather(request: HttpRequest | None) -> str:
    gather_action = absolute_url(
        request, "channels_app:voice-gather"
    )
    ga = escape_twiml_attr(gather_action)
    inner = (
        '<Say voice="Polly.Joanna">'
        "Thanks for calling. Please tell us how we can help after the tone."
        "</Say>"
        f'<Gather input="speech" action="{ga}" '
        'method="POST" speechTimeout="auto" language="en-US" '
        'speechModel="phone_call" enhanced="true">'
        "<Pause length=\"1\"/>"
        "</Gather>"
        f'<Redirect method="POST">{escape_twiml_text(gather_action)}</Redirect>'
    )
    return twiml_document(inner)


def twiml_escalation_handoff(request: HttpRequest | None) -> str:
    forward = (getattr(settings, "VOICE_ESCALATION_FORWARD_NUMBER", "") or "").strip()
    gather_action = absolute_url(request, "channels_app:voice-gather")
    ga = escape_twiml_attr(gather_action)
    inner = (
        '<Say voice="Polly.Joanna">'
        "Connecting you with a team member. Please stay on the line."
        "</Say>"
    )
    if forward:
        inner += (
            f'<Dial timeout="55"><Number>{escape_twiml_text(forward)}</Number></Dial>'
        )
        inner += (
            '<Say voice="Polly.Joanna">'
            "We could not complete the transfer. You can leave a message by speaking now."
            "</Say>"
        )
    else:
        inner += (
            '<Say voice="Polly.Joanna">'
            "A team member will join this line as soon as possible. "
            "Please hold, or speak after the tone to leave another message."
            "</Say>"
        )
    inner += (
        f'<Gather input="speech" action="{ga}" '
        'method="POST" speechTimeout="auto" language="en-US" '
        'speechModel="phone_call" enhanced="true">'
        "<Pause length=\"1\"/>"
        "</Gather>"
        f'<Redirect method="POST">{escape_twiml_text(gather_action)}</Redirect>'
    )
    return twiml_document(inner)


def twiml_human_only_hold(request: HttpRequest | None) -> str:
    gather_action = absolute_url(request, "channels_app:voice-gather")
    ga = escape_twiml_attr(gather_action)
    inner = (
        '<Say voice="Polly.Joanna">'
        "Thank you. A team member will speak with you shortly. "
        "You can say more after the tone."
        "</Say>"
        f'<Gather input="speech" action="{ga}" '
        'method="POST" speechTimeout="auto" language="en-US" '
        'speechModel="phone_call" enhanced="true">'
        "<Pause length=\"1\"/>"
        "</Gather>"
        f'<Redirect method="POST">{escape_twiml_text(gather_action)}</Redirect>'
    )
    return twiml_document(inner)


def redirect_call_with_twiml(call_sid: str, twiml_xml: str) -> bool:
    account = getattr(settings, "TWILIO_ACCOUNT_SID", "") or ""
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "") or ""
    if not account or not token or not call_sid:
        return False
    try:
        from twilio.rest import Client
    except ImportError:
        logger.warning("twilio not installed — cannot redirect live call")
        return False
    try:
        client = Client(account, token)
        client.calls(call_sid).update(twiml=twiml_xml)
        return True
    except Exception as exc:
        logger.exception("Twilio redirect failed: %s", exc)
        return False


def inject_agent_voice_message(
    request: HttpRequest | None,
    call_sid: str,
    message: str,
) -> bool:
    """Play agent text to the caller and resume the gather loop."""
    if not message.strip():
        return False
    play_url = None
    audio = synthesize_elevenlabs_mp3(message)
    if audio:
        file_id = write_tts_file(audio)
        play_url = absolute_url(
            request,
            "channels_app:voice-tts-media",
            file_id=file_id,
        )
    twiml = twiml_gather_loop(request, prompt_say=message if not play_url else None, play_url=play_url)
    return redirect_call_with_twiml(call_sid, twiml)


def process_speech_for_voice_pipeline(
    request: HttpRequest | None,
    call_sid: str,
    caller_e164: str,
    speech_result: str,
    confidence: str,
) -> str:
    """Persist STT, run AI pipeline, return TwiML string."""
    from core.models import Conversation, Message
    from core.views import process_message_internal
    from teams.tenant import get_default_team

    speech = (speech_result or "").strip()
    sender_name = caller_e164

    team = get_default_team()
    if team is None:
        logger.error("Voice pipeline: no Team row in database")
        return twiml_gather_loop(
            request,
            prompt_say="Service is not configured. Please try again later.",
        )

    conversation = (
        Conversation.objects.filter(
            team=team,
            sender_id=caller_e164,
            channel="voice",
        )
        .exclude(status="resolved")
        .order_by("-created_at")
        .first()
    )
    if conversation is None:
        conversation = Conversation.objects.create(
            team=team,
            sender_id=caller_e164,
            channel="voice",
            sender_name=sender_name,
        )

    conversation.last_voice_call_sid = call_sid
    conversation.save(update_fields=["last_voice_call_sid", "updated_at"])

    stt_meta = {
        "source": "voice_stt",
        "twilio_call_sid": call_sid,
        "stt_confidence": confidence,
    }

    if not speech:
        return twiml_gather_loop(
            request,
            prompt_say="Sorry, I did not catch that. Please try again.",
        )

    Message.objects.create(
        conversation=conversation,
        role="customer",
        content=speech,
        metadata=stt_meta,
    )

    if conversation.human_only:
        return twiml_human_only_hold(request)

    result = process_message_internal(
        message=speech,
        sender_id=caller_e164,
        sender_name=sender_name,
        channel="voice",
        conversation=conversation,
        skip_save_customer_message=True,
        ai_response_metadata={"source": "voice_ai"},
    )

    if result.get("human_only"):
        return twiml_human_only_hold(request)

    if result.get("escalated"):
        return twiml_escalation_handoff(request)

    reply = (result.get("response") or "").strip()
    if not reply:
        return twiml_gather_loop(
            request,
            prompt_say="I am not sure how to help with that. Could you rephrase?",
        )

    play_url = None
    audio = synthesize_elevenlabs_mp3(reply)
    if audio:
        file_id = write_tts_file(audio)
        play_url = absolute_url(
            request,
            "channels_app:voice-tts-media",
            file_id=file_id,
        )
    return twiml_gather_loop(
        request,
        prompt_say=reply if not play_url else None,
        play_url=play_url,
    )
