# Generated manually — route outbound WhatsApp to the same WABA number as inbound

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_voice_channel_last_voice_call_sid"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="whatsapp_phone_number_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Meta WhatsApp Cloud API phone_number_id this thread uses (for outbound replies).",
                max_length=64,
            ),
        ),
    ]
