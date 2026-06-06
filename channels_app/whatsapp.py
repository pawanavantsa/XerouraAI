import logging
from typing import Optional

import requests
from django.conf import settings

from .unified import UnifiedMessage

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"


def _unified_from_whatsapp_value(value: dict) -> Optional[UnifiedMessage]:
    """Build UnifiedMessage from one webhook ``value`` object, or None."""
    messages = value.get("messages")
    if not messages:
        return None

    message_obj = messages[0]
    message_type = message_obj.get("type", "")

    if message_type == "text":
        text_body = message_obj.get("text", {}).get("body", "")
    elif message_type == "interactive":
        interactive = message_obj.get("interactive", {})
        interactive_type = interactive.get("type", "")
        if interactive_type == "button_reply":
            text_body = interactive.get("button_reply", {}).get("title", "")
        elif interactive_type == "list_reply":
            text_body = interactive.get("list_reply", {}).get("title", "")
        else:
            text_body = ""
    else:
        logger.info("Unsupported WhatsApp message type: %s", message_type)
        return None

    if not text_body:
        return None

    contacts = value.get("contacts", [])
    sender_name = "Unknown"
    if contacts:
        sender_name = contacts[0].get("profile", {}).get("name", "Unknown")

    sender_id = message_obj.get("from", "")
    message_id = message_obj.get("id", "")
    phone_number_id = value.get("metadata", {}).get("phone_number_id", "")

    return UnifiedMessage(
        channel="whatsapp",
        sender_id=sender_id,
        sender_name=sender_name,
        message=text_body,
        conversation_id=sender_id,
        metadata={
            "message_id": message_id,
            "phone_number_id": phone_number_id,
            "message_type": message_type,
        },
    )


def parse_whatsapp_webhook(payload: dict) -> Optional[UnifiedMessage]:
    """
    Parse WhatsApp Cloud API webhook payload. Walks every ``entry`` and ``changes``
    item so a leading status update does not hide the user message.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            return None

        for ent in entry:
            for change in ent.get("changes", []):
                value = change.get("value", {})
                unified = _unified_from_whatsapp_value(value)
                if unified is not None:
                    return unified

        return None

    except (KeyError, IndexError, TypeError) as exc:
        logger.exception("Failed to parse WhatsApp webhook payload: %s", exc)
        return None


def _get_whatsapp_credentials(
    business_phone_number_id: str | None = None,
) -> tuple[str, str]:
    """Resolve access token + phone_number_id for outbound sends.

    If ``business_phone_number_id`` is set (from the inbound webhook), prefer the
    **matching** ``TeamWhatsAppConfig`` row. Otherwise the first active team
    config is used. Mismatched token vs. phone_number_id is a common reason
    replies never reach WhatsApp while the dashboard still shows them.
    """
    try:
        from teams.models import TeamWhatsAppConfig

        qs = TeamWhatsAppConfig.objects.filter(is_active=True)
        if business_phone_number_id:
            config = qs.filter(phone_number_id=business_phone_number_id).first()
            if config and config.access_token and config.phone_number_id:
                return config.access_token, config.phone_number_id
        config = qs.first()
        if config and config.access_token and config.phone_number_id:
            return config.access_token, config.phone_number_id
    except Exception:
        logger.exception("Failed to load TeamWhatsAppConfig")

    return (
        getattr(settings, "WHATSAPP_ACCESS_TOKEN", ""),
        getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", ""),
    )


def send_whatsapp_message(
    phone_number: str,
    message: str,
    *,
    business_phone_number_id: str | None = None,
) -> bool:
    """
    Send a text message to a WhatsApp user via the Cloud API.

    Reads credentials from team config in database first, falls back to .env.
    """
    access_token, phone_number_id = _get_whatsapp_credentials(
        business_phone_number_id
    )

    if not access_token or not phone_number_id:
        logger.error(
            "WhatsApp credentials not configured. "
            "Configure via Settings > WhatsApp in the dashboard "
            "or WHATSAPP_ACCESS_TOKEN + WHATSAPP_PHONE_NUMBER_ID in .env."
        )
        return False

    url = f"{WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if not response.ok:
            logger.error(
                "WhatsApp API error HTTP %s for to=%s phone_number_id=%s body=%s",
                response.status_code,
                phone_number,
                phone_number_id,
                response.text[:2000],
            )
        response.raise_for_status()
        logger.info("WhatsApp message sent to %s", phone_number)
        return True
    except requests.RequestException as exc:
        logger.exception(
            "Failed to send WhatsApp message to %s (phone_number_id=%s): %s",
            phone_number,
            phone_number_id,
            exc,
        )
        return False
