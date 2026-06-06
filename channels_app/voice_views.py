"""Twilio Voice webhooks and short-lived TTS media URLs."""

import logging
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import FormParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .voice_service import (
    process_speech_for_voice_pipeline,
    twiml_welcome_then_gather,
    validate_twilio_signature,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TwilioVoiceIncomingView(APIView):
    """First leg when a customer calls your Twilio number (POST)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [FormParser]

    def post(self, request):
        if not validate_twilio_signature(request):
            return HttpResponse("Forbidden", status=403)
        xml = twiml_welcome_then_gather(request)
        return HttpResponse(xml, content_type="text/xml; charset=utf-8")


@method_decorator(csrf_exempt, name="dispatch")
class TwilioVoiceGatherView(APIView):
    """Twilio posts speech recognition results here (POST)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [FormParser]

    def post(self, request):
        if not validate_twilio_signature(request):
            return HttpResponse("Forbidden", status=403)

        call_sid = (request.POST.get("CallSid") or "").strip()
        from_raw = (request.POST.get("From") or "").strip()
        speech = (request.POST.get("SpeechResult") or "").strip()
        confidence = (request.POST.get("Confidence") or "").strip()

        if not call_sid or not from_raw:
            logger.warning("Voice gather missing CallSid or From")
            xml = twiml_welcome_then_gather(request)
            return HttpResponse(xml, content_type="text/xml; charset=utf-8")

        try:
            xml = process_speech_for_voice_pipeline(
                request,
                call_sid=call_sid,
                caller_e164=from_raw,
                speech_result=speech,
                confidence=confidence,
            )
        except Exception:
            logger.exception("Voice pipeline failed for call %s", call_sid)
            xml = twiml_welcome_then_gather(request)

        return HttpResponse(xml, content_type="text/xml; charset=utf-8")


class VoiceTtsMediaView(APIView):
    """Public GET for Twilio <Play> — short-lived files under MEDIA_ROOT/voice_tts."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, file_id):
        path = Path(settings.MEDIA_ROOT) / "voice_tts" / f"{file_id}.mp3"
        if not path.is_file():
            raise Http404
        return FileResponse(path.open("rb"), content_type="audio/mpeg")
