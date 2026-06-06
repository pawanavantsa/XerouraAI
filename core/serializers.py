from rest_framework import serializers

from .models import (
    CannedResponse,
    Conversation,
    InternalNote,
    KnowledgeBase,
    Message,
    Tag,
)


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = [
            "id",
            "team_id",
            "content",
            "category",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "team_id", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "content", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "team_id", "name", "color", "created_at"]
        read_only_fields = ["id", "team_id", "created_at"]


class InternalNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalNote
        fields = ["id", "conversation", "author_name", "content", "created_at"]
        read_only_fields = ["id", "conversation", "created_at"]


class CannedResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CannedResponse
        fields = [
            "id",
            "team_id",
            "title",
            "content",
            "category",
            "shortcut",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "team_id", "created_at", "updated_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    internal_notes = InternalNoteSerializer(many=True, read_only=True)
    escalation_id = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "team_id",
            "channel",
            "sender_id",
            "sender_name",
            "status",
            "assigned_agent",
            "human_only",
            "last_voice_call_sid",
            "created_at",
            "updated_at",
            "messages",
            "tags",
            "internal_notes",
            "escalation_id",
        ]
        read_only_fields = ["id", "team_id", "created_at", "updated_at"]

    def get_escalation_id(self, obj) -> str | None:
        escalation = obj.escalations.filter(resolved=False).first()
        return str(escalation.id) if escalation else None


class VoiceCallQueueSerializer(serializers.ModelSerializer):
    """Voice-only queue row for the Calls dashboard."""

    escalation_id = serializers.SerializerMethodField()
    needs_human = serializers.SerializerMethodField()
    has_live_call_hint = serializers.SerializerMethodField()
    last_customer_preview = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "sender_id",
            "sender_name",
            "status",
            "human_only",
            "last_voice_call_sid",
            "created_at",
            "updated_at",
            "escalation_id",
            "needs_human",
            "has_live_call_hint",
            "last_customer_preview",
        ]
        read_only_fields = fields

    def get_escalation_id(self, obj) -> str | None:
        esc = obj.escalations.filter(resolved=False).first()
        return str(esc.id) if esc else None

    def get_needs_human(self, obj) -> bool:
        if getattr(obj, "human_only", False):
            return True
        if obj.status == "escalated":
            return True
        return obj.escalations.filter(resolved=False).exists()

    def get_has_live_call_hint(self, obj) -> bool:
        return bool((obj.last_voice_call_sid or "").strip())

    def get_last_customer_preview(self, obj) -> str:
        text = getattr(obj, "_last_customer_preview", None) or ""
        text = text.strip()
        if len(text) > 140:
            return text[:137] + "…"
        return text


class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source="messages.count", read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "team_id",
            "channel",
            "sender_id",
            "sender_name",
            "status",
            "assigned_agent",
            "created_at",
            "updated_at",
            "message_count",
            "tags",
        ]
        read_only_fields = ["id", "team_id", "created_at", "updated_at"]


class ConversationSearchSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source="messages.count", read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "team_id",
            "channel",
            "sender_id",
            "sender_name",
            "status",
            "assigned_agent",
            "created_at",
            "updated_at",
            "message_count",
            "tags",
        ]
        read_only_fields = ["id", "team_id", "created_at", "updated_at"]


class ProcessMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    sender_id = serializers.CharField()
    channel = serializers.ChoiceField(choices=["whatsapp", "email", "webchat", "telegram", "messenger", "instagram"])
    sender_name = serializers.CharField(required=False, default="")
    team_id = serializers.UUIDField(required=False, allow_null=True)
