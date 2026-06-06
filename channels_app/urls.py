from django.urls import path

from .views import EmailWebhookView, GmailPollView, MessengerWebhookView, TelegramWebhookView, WhatsAppWebhookView
from .voice_views import (
    TwilioVoiceGatherView,
    TwilioVoiceIncomingView,
    VoiceTtsMediaView,
)

app_name = "channels_app"

urlpatterns = [
    path(
        "webhooks/whatsapp/",
        WhatsAppWebhookView.as_view(),
        name="whatsapp-webhook",
    ),
    path(
        "webhooks/email/",
        EmailWebhookView.as_view(),
        name="email-webhook",
    ),
    path(
        "email/poll/",
        GmailPollView.as_view(),
        name="gmail-poll",
    ),
    path(
        "webhooks/telegram/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
    ),
    path(
        "webhooks/telegram/<uuid:team_id>/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook-team",
    ),
    path(
        "webhooks/messenger/",
        MessengerWebhookView.as_view(),
        name="messenger-webhook",
    ),
    path(
        "webhooks/voice/incoming/",
        TwilioVoiceIncomingView.as_view(),
        name="voice-incoming",
    ),
    path(
        "webhooks/voice/gather/",
        TwilioVoiceGatherView.as_view(),
        name="voice-gather",
    ),
    path(
        "media/voice/<uuid:file_id>/",
        VoiceTtsMediaView.as_view(),
        name="voice-tts-media",
    ),
]
