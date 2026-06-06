import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def assign_default_team(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    team = Team.objects.order_by("created_at").first()
    if team is None:
        team = Team.objects.create(
            name="Default organization",
            slug="default",
            plan="free",
        )
    KnowledgeBase = apps.get_model("core", "KnowledgeBase")
    Conversation = apps.get_model("core", "Conversation")
    Tag = apps.get_model("core", "Tag")
    CannedResponse = apps.get_model("core", "CannedResponse")
    KnowledgeBase.objects.filter(team_id__isnull=True).update(team_id=team.pk)
    Conversation.objects.filter(team_id__isnull=True).update(team_id=team.pk)
    Tag.objects.filter(team_id__isnull=True).update(team_id=team.pk)
    CannedResponse.objects.filter(team_id__isnull=True).update(team_id=team.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_conversation_whatsapp_phone_number_id"),
        ("teams", "0006_teamgmailconfig_last_poll_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgebase",
            name="team",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="knowledge_entries",
                to="teams.team",
            ),
        ),
        migrations.AddField(
            model_name="conversation",
            name="team",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="conversations",
                to="teams.team",
            ),
        ),
        migrations.AddField(
            model_name="tag",
            name="team",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tags",
                to="teams.team",
            ),
        ),
        migrations.AddField(
            model_name="cannedresponse",
            name="team",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="canned_responses",
                to="teams.team",
            ),
        ),
        migrations.RunPython(assign_default_team, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="knowledgebase",
            name="team",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="knowledge_entries",
                to="teams.team",
            ),
        ),
        migrations.AlterField(
            model_name="conversation",
            name="team",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="conversations",
                to="teams.team",
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="team",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tags",
                to="teams.team",
            ),
        ),
        migrations.AlterField(
            model_name="cannedresponse",
            name="team",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="canned_responses",
                to="teams.team",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="conversation",
            name="unique_active_conversation_per_sender_channel",
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.UniqueConstraint(
                condition=models.Q(status__in=["active", "escalated"]),
                fields=("team", "sender_id", "channel"),
                name="unique_active_conversation_per_team_sender_channel",
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="name",
            field=models.CharField(max_length=50),
        ),
        migrations.AddConstraint(
            model_name="tag",
            constraint=models.UniqueConstraint(
                fields=("team", "name"),
                name="core_tag_team_name_uniq",
            ),
        ),
        migrations.AlterField(
            model_name="cannedresponse",
            name="shortcut",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddConstraint(
            model_name="cannedresponse",
            constraint=models.UniqueConstraint(
                condition=~Q(shortcut=""),
                fields=("team", "shortcut"),
                name="core_canned_team_shortcut_non_empty_uniq",
            ),
        ),
    ]
