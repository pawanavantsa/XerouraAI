# Generated manually for voice channel support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_conversation_channel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversation",
            name="channel",
            field=models.CharField(
                choices=[
                    ("whatsapp", "WhatsApp"),
                    ("email", "Email"),
                    ("webchat", "Web Chat"),
                    ("telegram", "Telegram"),
                    ("messenger", "Messenger"),
                    ("instagram", "Instagram"),
                    ("voice", "Voice (Phone)"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="conversation",
            name="last_voice_call_sid",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Most recent Twilio CallSid for this thread (used to inject live agent audio).",
                max_length=64,
            ),
        ),
    ]
