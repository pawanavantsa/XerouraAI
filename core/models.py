import uuid

from django.db import models
from pgvector.django import VectorField


class KnowledgeBase(models.Model):
    CATEGORY_CHOICES = [
        ("billing", "Billing"),
        ("technical", "Technical"),
        ("account", "Account"),
        ("general", "General"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="knowledge_entries",
    )
    content = models.TextField()
    embedding = VectorField(dimensions=1536)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_base"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.category}] {self.content[:80]}"


class Conversation(models.Model):
    CHANNEL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("email", "Email"),
        ("webchat", "Web Chat"),
        ("telegram", "Telegram"),
        ("messenger", "Messenger"),
        ("instagram", "Instagram"),
        ("voice", "Voice (Phone)"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("escalated", "Escalated"),
        ("resolved", "Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    sender_id = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    assigned_agent = models.CharField(max_length=255, blank=True, null=True)
    human_only = models.BooleanField(default=False)
    last_voice_call_sid = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Most recent Twilio CallSid for this thread (used to inject live agent audio).",
    )
    whatsapp_phone_number_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Meta WhatsApp Cloud API phone_number_id this thread uses (for outbound replies).",
    )
    tags = models.ManyToManyField(
        "Tag", through="ConversationTag", related_name="conversations", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "sender_id", "channel"],
                condition=models.Q(status__in=["active", "escalated"]),
                name="unique_active_conversation_per_team_sender_channel",
            )
        ]
        indexes = [
            models.Index(fields=["sender_id", "channel", "status"]),
        ]

    def __str__(self):
        return f"{self.channel} - {self.sender_id} ({self.status})"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#6366f1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"],
                name="core_tag_team_name_uniq",
            ),
        ]

    def __str__(self):
        return self.name


class ConversationTag(models.Model):
    conversation = models.ForeignKey(
        "Conversation", on_delete=models.CASCADE
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = "conversation_tags"
        unique_together = [("conversation", "tag")]

    def __str__(self):
        return f"{self.conversation_id} - {self.tag.name}"


class Message(models.Model):
    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("ai", "AI"),
        ("agent", "Agent"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


class InternalNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="internal_notes"
    )
    author_name = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "internal_notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.author_name}] {self.content[:60]}"


class CannedResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="canned_responses",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, blank=True, default="")
    shortcut = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canned_responses"
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "shortcut"],
                condition=~models.Q(shortcut=""),
                name="core_canned_team_shortcut_non_empty_uniq",
            ),
        ]

    def __str__(self):
        return self.title
