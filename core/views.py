import logging

from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Case, Exists, IntegerField, OuterRef, Q, Subquery, Value, When
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny

from teams.permissions import HasTeamContext
from rest_framework.response import Response
from rest_framework.views import APIView

from .classifier import classify_ticket
from .embeddings import chunk_text, generate_embedding
from .guardrails import check_response
from .knowledge_base import search_knowledge_base
from .models import (
    CannedResponse,
    Conversation,
    ConversationTag,
    InternalNote,
    KnowledgeBase,
    Message,
    Tag,
)
from .responder import generate_response
from .serializers import (
    CannedResponseSerializer,
    ConversationListSerializer,
    ConversationSearchSerializer,
    ConversationSerializer,
    InternalNoteSerializer,
    KnowledgeBaseSerializer,
    ProcessMessageSerializer,
    TagSerializer,
    VoiceCallQueueSerializer,
)

logger = logging.getLogger(__name__)


def _resolve_team_for_request(request, validated_data: dict | None = None):
    """Resolve Team from JWT/API key, optional body team_id, or default org."""
    from teams.models import Team
    from teams.tenant import get_default_team

    team = getattr(request, "team", None) if request is not None else None
    if team is not None:
        return team
    tid = (validated_data or {}).get("team_id")
    if tid is not None:
        t = Team.objects.filter(pk=tid).first()
        if t is not None:
            return t
    return get_default_team()


def process_message_internal(
    message: str,
    sender_id: str,
    sender_name: str = "",
    channel: str = "webchat",
    *,
    conversation: Conversation | None = None,
    team=None,
    skip_save_customer_message: bool = False,
    customer_message_metadata: dict | None = None,
    ai_response_metadata: dict | None = None,
) -> dict:
    """Core message processing pipeline. Used by all channels (WhatsApp, Email, WebChat, Voice).

    If ``conversation`` is provided, it is used instead of looking up by sender/channel.
    ``team`` scopes new lookups and creates (required unless ``conversation`` is passed or
    a default team exists).
    If ``skip_save_customer_message`` is True, the caller must already have persisted the
    customer turn (e.g. voice STT) — only the AI pipeline runs.

    Returns dict with: response, classification, conversation_id, escalated
    """
    from teams.tenant import get_default_team

    if conversation is not None:
        if team is not None and team.id != conversation.team_id:
            logger.warning(
                "process_message_internal: ignoring mismatched team for conversation %s",
                conversation.id,
            )
        team = conversation.team
    else:
        if team is None:
            team = get_default_team()
        if team is None:
            logger.error("process_message_internal: no team context and no default Team row")
            raise ValueError("No team context for conversation")

        # Find existing open conversation or create a new one (race-condition safe)
        conversation = (
            Conversation.objects.filter(
                team_id=team.id,
                sender_id=sender_id,
                channel=channel,
            )
            .exclude(status="resolved")
            .order_by("-created_at")
            .first()
        )
        if conversation is None:
            try:
                conversation = Conversation.objects.create(
                    team=team,
                    sender_id=sender_id,
                    channel=channel,
                    sender_name=sender_name or sender_id,
                )
            except Exception:
                # Race condition: another request created it first
                conversation = (
                    Conversation.objects.filter(
                        team_id=team.id,
                        sender_id=sender_id,
                        channel=channel,
                    )
                    .exclude(status="resolved")
                    .order_by("-created_at")
                    .first()
                )
    if (
        conversation.sender_id != sender_id
        or conversation.channel != channel
    ):
        logger.warning(
            "process_message_internal: conversation %s sender/channel mismatch "
            "(expected %s/%s, got %s/%s)",
            conversation.id,
            conversation.sender_id,
            conversation.channel,
            sender_id,
            channel,
        )

    # Save customer message (unless voice/STT path already saved it)
    if not skip_save_customer_message:
        Message.objects.create(
            conversation=conversation,
            role="customer",
            content=message,
            metadata=customer_message_metadata or {},
        )

    # If human-only mode is on, skip AI entirely — wait for human agent
    if conversation.human_only:
        logger.info(
            "Human-only mode for conversation %s — skipping AI pipeline",
            conversation.id,
        )
        return {
            "response": None,
            "classification": {"category": "human_only", "confidence": 1.0, "reasoning": "Human-only mode enabled"},
            "conversation_id": str(conversation.id),
            "escalated": False,
            "human_only": True,
            "resolved": False,
        }

    # Classify with Haiku
    classification = classify_ticket(message)

    # Previous AI asked if the issue is resolved — handle yes (close) / no (escalate) before other escalation.
    if conversation.status == "active":
        try:
            from escalation.detector import (
                DEFAULT_HANDOFF_REPLY,
                DEFAULT_RESOLVED_CLOSING_REPLY,
                ai_message_asks_additional_help_question,
                ai_message_asks_issue_fixed_question,
                ai_message_asks_resolution_followup,
                last_ai_message_before_latest_customer,
                user_confirms_issue_resolved,
                user_indicates_issue_still_broken,
                user_means_no_further_help,
            )
            from escalation.handoff import create_handoff_package

            prev_ai = last_ai_message_before_latest_customer(conversation)
            if prev_ai and ai_message_asks_resolution_followup(prev_ai):
                issue_asks = ai_message_asks_issue_fixed_question(prev_ai)
                more_help = ai_message_asks_additional_help_question(prev_ai)

                if user_confirms_issue_resolved(message):
                    conversation.status = "resolved"
                    conversation.save(update_fields=["status", "updated_at"])
                    out = DEFAULT_RESOLVED_CLOSING_REPLY
                    Message.objects.create(
                        conversation=conversation,
                        role="ai",
                        content=out,
                        metadata={"resolved": True, "resolution_confirmed": True},
                    )
                    return {
                        "response": out,
                        "classification": classification,
                        "conversation_id": str(conversation.id),
                        "escalated": False,
                        "resolved": True,
                    }
                # "Anything else you need?" → no = nothing more to do; close the ticket.
                if more_help and user_means_no_further_help(message):
                    conversation.status = "resolved"
                    conversation.save(update_fields=["status", "updated_at"])
                    out = DEFAULT_RESOLVED_CLOSING_REPLY
                    Message.objects.create(
                        conversation=conversation,
                        role="ai",
                        content=out,
                        metadata={"resolved": True, "resolution_confirmed": True, "followup": "no_more_help"},
                    )
                    return {
                        "response": out,
                        "classification": classification,
                        "conversation_id": str(conversation.id),
                        "escalated": False,
                        "resolved": True,
                    }
                if user_indicates_issue_still_broken(
                    message, issue_asks=issue_asks, more_help=more_help
                ):
                    conversation.status = "escalated"
                    conversation.save(update_fields=["status", "updated_at"])
                    try:
                        create_handoff_package(
                            conversation_id=str(conversation.id),
                            reason="customer_request",
                            details=(
                                "Customer indicated the issue is not resolved after the assistant "
                                "asked for status or follow-up."
                            ),
                        )
                    except Exception as e:
                        logger.error("Failed to create handoff package: %s", str(e))
                    out = DEFAULT_HANDOFF_REPLY
                    Message.objects.create(
                        conversation=conversation,
                        role="ai",
                        content=out,
                        metadata={
                            "escalated": True,
                            "reason": "customer_request",
                            "escalation_trigger": "resolution_denied",
                        },
                    )
                    return {
                        "response": out,
                        "classification": classification,
                        "conversation_id": str(conversation.id),
                        "escalated": True,
                        "escalation_reason": "customer_request",
                        "resolved": False,
                    }
        except Exception as e:
            logger.exception("Resolution follow-up handling failed: %s", e)

    # Check for escalation
    try:
        from escalation.detector import DEFAULT_HANDOFF_REPLY, should_escalate
        from escalation.handoff import create_handoff_package

        escalation_result = should_escalate(message, classification, conversation)
    except Exception as e:
        logger.error("Escalation check failed: %s", str(e))
        escalation_result = {"should_escalate": False}

    if escalation_result.get("should_escalate"):
        conversation.status = "escalated"
        conversation.save(update_fields=["status", "updated_at"])

        try:
            create_handoff_package(
                conversation_id=str(conversation.id),
                reason=escalation_result.get("reason", "customer_request"),
                details=escalation_result.get("details", ""),
            )
        except Exception as e:
            logger.error("Failed to create handoff package: %s", str(e))

        ai_response = DEFAULT_HANDOFF_REPLY
        esc_meta = {
            "escalated": True,
            "reason": escalation_result.get("reason", ""),
        }
        if ai_response_metadata:
            esc_meta.update(ai_response_metadata)
        Message.objects.create(
            conversation=conversation,
            role="ai",
            content=ai_response,
            metadata=esc_meta,
        )

        return {
            "response": ai_response,
            "classification": classification,
            "conversation_id": str(conversation.id),
            "escalated": True,
            "escalation_reason": escalation_result.get("reason", ""),
            "resolved": False,
        }

    # Retrieve knowledge base context
    query_embedding = generate_embedding(message)
    knowledge_chunks = search_knowledge_base(
        query_embedding=query_embedding,
        team_id=conversation.team_id,
        category=classification.get("category"),
        limit=3,
    )

    # Build conversation history
    history = list(
        Message.objects.filter(conversation=conversation)
        .order_by("created_at")
        .values("role", "content")
    )
    history = history[:-1]  # Exclude the message we just saved

    # Generate response with Sonnet
    response_result = generate_response(
        message=message,
        conversation_history=history,
        knowledge_chunks=knowledge_chunks,
    )

    # Run guardrails
    guardrail_result = check_response(
        response=response_result["response"],
        knowledge_chunks=knowledge_chunks,
    )

    ai_response = response_result["response"]

    if not guardrail_result["is_safe"]:
        logger.warning(
            "Guardrails flagged response for conversation %s: %s",
            conversation.id,
            guardrail_result["flagged_terms"],
        )

    # If the model offered a teammate / human in its reply, escalate the ticket (same as explicit human request).
    try:
        from escalation.detector import assistant_response_offers_handoff
        from escalation.handoff import create_handoff_package

        if (
            conversation.status != "escalated"
            and assistant_response_offers_handoff(ai_response)
        ):
            conversation.status = "escalated"
            conversation.save(update_fields=["status", "updated_at"])
            try:
                create_handoff_package(
                    conversation_id=str(conversation.id),
                    reason="customer_request",
                    details=(
                        "Assistant reply offered connection to a teammate or human support "
                        "(detected from model wording, e.g. no KB match)."
                    ),
                )
            except Exception as e:
                logger.error("Failed to create handoff package: %s", str(e))

            esc_meta = {
                "escalated": True,
                "reason": "customer_request",
                "escalation_trigger": "ai_offered_handoff",
                "confidence": response_result["confidence"],
                "guardrails": guardrail_result,
                "classification": classification,
            }
            if ai_response_metadata:
                esc_meta.update(ai_response_metadata)
            Message.objects.create(
                conversation=conversation,
                role="ai",
                content=ai_response,
                metadata=esc_meta,
            )

            return {
                "response": ai_response,
                "classification": classification,
                "conversation_id": str(conversation.id),
                "escalated": True,
                "escalation_reason": "customer_request",
                "resolved": False,
            }
    except Exception as e:
        logger.error("Handoff detection after generate_response failed: %s", str(e))

    # Save AI response
    normal_meta = {
        "confidence": response_result["confidence"],
        "guardrails": guardrail_result,
        "classification": classification,
    }
    if ai_response_metadata:
        normal_meta.update(ai_response_metadata)
    Message.objects.create(
        conversation=conversation,
        role="ai",
        content=ai_response,
        metadata=normal_meta,
    )

    return {
        "response": ai_response,
        "classification": classification,
        "conversation_id": str(conversation.id),
        "escalated": False,
        "resolved": False,
    }


class ProcessMessageView(APIView):
    """Main orchestrator endpoint. Takes a customer message, classifies it,
    retrieves knowledge base context, generates a response, and runs guardrails.
    """

    def post(self, request):
        serializer = ProcessMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        message = data["message"]
        sender_id = data["sender_id"]
        channel = data["channel"]
        sender_name = data.get("sender_name", "")

        team = _resolve_team_for_request(request, data)
        if team is None:
            return Response(
                {"error": "No team context. Create a team, sign in, or pass team_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Find existing open conversation or create a new one (race-condition safe)
        conversation = (
            Conversation.objects.filter(
                team_id=team.id,
                sender_id=sender_id,
                channel=channel,
            )
            .exclude(status="resolved")
            .order_by("-created_at")
            .first()
        )
        if conversation is None:
            try:
                conversation = Conversation.objects.create(
                    team=team,
                    sender_id=sender_id,
                    channel=channel,
                    sender_name=sender_name or sender_id,
                )
            except Exception:
                conversation = (
                    Conversation.objects.filter(
                        team_id=team.id,
                        sender_id=sender_id,
                        channel=channel,
                    )
                    .exclude(status="resolved")
                    .order_by("-created_at")
                    .first()
                )

        # 2. Save the customer message
        Message.objects.create(
            conversation=conversation,
            role="customer",
            content=message,
        )

        # 3. Classify the ticket
        classification = classify_ticket(message)
        category = classification["category"]

        # 3b. Resolution follow-up (same as process_message_internal)
        if conversation.status == "active":
            try:
                from escalation.detector import (
                    DEFAULT_HANDOFF_REPLY,
                    DEFAULT_RESOLVED_CLOSING_REPLY,
                    ai_message_asks_additional_help_question,
                    ai_message_asks_issue_fixed_question,
                    ai_message_asks_resolution_followup,
                    last_ai_message_before_latest_customer,
                    user_confirms_issue_resolved,
                    user_indicates_issue_still_broken,
                    user_means_no_further_help,
                )
                from escalation.handoff import create_handoff_package

                prev_ai = last_ai_message_before_latest_customer(conversation)
                if prev_ai and ai_message_asks_resolution_followup(prev_ai):
                    issue_asks = ai_message_asks_issue_fixed_question(prev_ai)
                    more_help = ai_message_asks_additional_help_question(prev_ai)

                    if user_confirms_issue_resolved(message):
                        conversation.status = "resolved"
                        conversation.save(update_fields=["status", "updated_at"])
                        out = DEFAULT_RESOLVED_CLOSING_REPLY
                        Message.objects.create(
                            conversation=conversation,
                            role="ai",
                            content=out,
                            metadata={"resolved": True, "resolution_confirmed": True},
                        )
                        return Response(
                            {
                                "conversation_id": str(conversation.id),
                                "classification": classification,
                                "escalated": False,
                                "resolved": True,
                                "response": out,
                            },
                            status=status.HTTP_200_OK,
                        )
                    if more_help and user_means_no_further_help(message):
                        conversation.status = "resolved"
                        conversation.save(update_fields=["status", "updated_at"])
                        out = DEFAULT_RESOLVED_CLOSING_REPLY
                        Message.objects.create(
                            conversation=conversation,
                            role="ai",
                            content=out,
                            metadata={
                                "resolved": True,
                                "resolution_confirmed": True,
                                "followup": "no_more_help",
                            },
                        )
                        return Response(
                            {
                                "conversation_id": str(conversation.id),
                                "classification": classification,
                                "escalated": False,
                                "resolved": True,
                                "response": out,
                            },
                            status=status.HTTP_200_OK,
                        )
                    if user_indicates_issue_still_broken(
                        message, issue_asks=issue_asks, more_help=more_help
                    ):
                        conversation.status = "escalated"
                        conversation.save(update_fields=["status", "updated_at"])
                        try:
                            create_handoff_package(
                                conversation_id=str(conversation.id),
                                reason="customer_request",
                                details=(
                                    "Customer indicated the issue is not resolved after the assistant "
                                    "asked for status or follow-up."
                                ),
                            )
                        except Exception as e:
                            logger.error("Failed to create handoff package: %s", str(e))
                        out = DEFAULT_HANDOFF_REPLY
                        Message.objects.create(
                            conversation=conversation,
                            role="ai",
                            content=out,
                            metadata={
                                "escalated": True,
                                "reason": "customer_request",
                                "escalation_trigger": "resolution_denied",
                            },
                        )
                        return Response(
                            {
                                "conversation_id": str(conversation.id),
                                "classification": classification,
                                "escalated": True,
                                "escalation_reason": "customer_request",
                                "resolved": False,
                                "response": out,
                            },
                            status=status.HTTP_200_OK,
                        )
            except Exception as e:
                logger.exception("Resolution follow-up handling failed: %s", e)

        # 4. Check for escalation
        try:
            from escalation.detector import DEFAULT_HANDOFF_REPLY, should_escalate
            from escalation.handoff import create_handoff_package

            escalation_result = should_escalate(message, classification, conversation)
        except ImportError:
            logger.warning("escalation.detector not available, skipping escalation check")
            escalation_result = {"should_escalate": False}
        except Exception as e:
            logger.error("Escalation check failed: %s", str(e))
            escalation_result = {"should_escalate": False}

        if escalation_result.get("should_escalate"):
            conversation.status = "escalated"
            conversation.save(update_fields=["status", "updated_at"])

            try:
                create_handoff_package(
                    conversation_id=str(conversation.id),
                    reason=escalation_result.get("reason", "customer_request"),
                    details=escalation_result.get("details", ""),
                )
            except Exception as e:
                logger.error("Failed to create handoff package: %s", str(e))

            ai_response = DEFAULT_HANDOFF_REPLY
            Message.objects.create(
                conversation=conversation,
                role="ai",
                content=ai_response,
                metadata={"escalated": True, "reason": escalation_result.get("reason", "")},
            )

            return Response(
                {
                    "conversation_id": str(conversation.id),
                    "classification": classification,
                    "escalated": True,
                    "escalation_reason": escalation_result.get("reason", ""),
                    "resolved": False,
                    "response": ai_response,
                },
                status=status.HTTP_200_OK,
            )

        # 5. Generate embedding and retrieve knowledge base chunks
        query_embedding = generate_embedding(message)
        knowledge_chunks = search_knowledge_base(
            query_embedding=query_embedding,
            team_id=conversation.team_id,
            category=category,
            limit=3,
        )

        # 6. Build conversation history
        history = list(
            Message.objects.filter(conversation=conversation)
            .order_by("created_at")
            .values("role", "content")
        )
        # Exclude the message we just saved (it's included in the prompt directly)
        history = history[:-1]

        # 7. Generate response with Sonnet
        response_result = generate_response(
            message=message,
            conversation_history=history,
            knowledge_chunks=knowledge_chunks,
        )

        # 8. Run guardrails
        guardrail_result = check_response(
            response=response_result["response"],
            knowledge_chunks=knowledge_chunks,
        )

        ai_response = response_result["response"]

        # If guardrails flag the response, add a disclaimer
        if not guardrail_result["is_safe"]:
            logger.warning(
                "Guardrails flagged response for conversation %s: %s",
                conversation.id,
                guardrail_result["flagged_terms"],
            )

        # Escalate when the model's reply offers a teammate / human (align with process_message_internal).
        try:
            from escalation.detector import assistant_response_offers_handoff

            if (
                conversation.status != "escalated"
                and assistant_response_offers_handoff(ai_response)
            ):
                from escalation.handoff import create_handoff_package

                conversation.status = "escalated"
                conversation.save(update_fields=["status", "updated_at"])
                try:
                    create_handoff_package(
                        conversation_id=str(conversation.id),
                        reason="customer_request",
                        details=(
                            "Assistant reply offered connection to a teammate or human support "
                            "(detected from model wording)."
                        ),
                    )
                except Exception as e:
                    logger.error("Failed to create handoff package: %s", str(e))

                Message.objects.create(
                    conversation=conversation,
                    role="ai",
                    content=ai_response,
                    metadata={
                        "escalated": True,
                        "reason": "customer_request",
                        "escalation_trigger": "ai_offered_handoff",
                        "confidence": response_result["confidence"],
                        "guardrails": guardrail_result,
                        "classification": classification,
                    },
                )

                return Response(
                    {
                        "conversation_id": str(conversation.id),
                        "classification": classification,
                        "escalated": True,
                        "escalation_reason": "customer_request",
                        "resolved": False,
                        "response": ai_response,
                        "confidence": response_result["confidence"],
                        "guardrails": guardrail_result,
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            logger.error("Handoff detection after generate_response failed: %s", str(e))

        # 9. Save the AI response
        Message.objects.create(
            conversation=conversation,
            role="ai",
            content=ai_response,
            metadata={
                "confidence": response_result["confidence"],
                "guardrails": guardrail_result,
                "classification": classification,
            },
        )

        return Response(
            {
                "conversation_id": str(conversation.id),
                "classification": classification,
                "escalated": False,
                "resolved": False,
                "response": ai_response,
                "confidence": response_result["confidence"],
                "guardrails": guardrail_result,
            },
            status=status.HTTP_200_OK,
        )


class KnowledgeBaseListCreateView(generics.ListCreateAPIView):
    """List all knowledge base entries or add a new one."""

    permission_classes = [HasTeamContext]
    serializer_class = KnowledgeBaseSerializer

    def get_queryset(self):
        return KnowledgeBase.objects.filter(team=self.request.team).order_by("-created_at")

    def perform_create(self, serializer):
        content = serializer.validated_data["content"]
        embedding = generate_embedding(content)
        serializer.save(team=self.request.team, embedding=embedding)


class ConversationListView(generics.ListAPIView):
    """List conversations for the authenticated user's team."""

    permission_classes = [HasTeamContext]
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        return Conversation.objects.filter(team=self.request.team).prefetch_related("tags")


class ToggleHumanOnlyView(APIView):
    """POST — Toggle human-only mode on a conversation.

    When enabled, AI will not respond to new messages — only human agents can reply.
    """

    permission_classes = [HasTeamContext]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk, team=request.team)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Toggle or set explicitly
        human_only = request.data.get("human_only")
        if human_only is not None:
            conversation.human_only = bool(human_only)
        else:
            conversation.human_only = not conversation.human_only

        conversation.save(update_fields=["human_only", "updated_at"])

        return Response({
            "conversation_id": str(conversation.id),
            "human_only": conversation.human_only,
        })


class VoiceCallsQueueView(APIView):
    """GET — Active voice conversations for the Calls dashboard.

    Returns ``needs_attention_count`` (caller asked for human, escalated, or
    human-only) and a list sorted with those first. Used for sidebar badges
    and the dedicated Calls page.
    """

    permission_classes = [HasTeamContext]

    def get(self, request):
        from escalation.models import Escalation

        latest_customer = Subquery(
            Message.objects.filter(
                conversation_id=OuterRef("pk"),
                role="customer",
            )
            .order_by("-created_at")
            .values("content")[:1]
        )
        open_escalation = Escalation.objects.filter(
            conversation_id=OuterRef("pk"),
            resolved=False,
        )
        qs = (
            Conversation.objects.filter(team=request.team, channel="voice")
            .exclude(status="resolved")
            .annotate(_last_customer_preview=latest_customer)
            .annotate(_has_open_escalation=Exists(open_escalation))
            .annotate(
                _priority=Case(
                    When(
                        Q(status="escalated")
                        | Q(human_only=True)
                        | Q(_has_open_escalation=True),
                        then=Value(0),
                    ),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
            )
            .prefetch_related("escalations")
            .order_by("_priority", "-updated_at")
        )
        ser = VoiceCallQueueSerializer(qs, many=True)
        calls = ser.data
        needs = sum(1 for row in calls if row.get("needs_human"))
        return Response(
            {
                "needs_attention_count": needs,
                "calls": calls,
            }
        )


class ConversationDetailView(generics.RetrieveAPIView):
    """Get a single conversation with all its messages."""

    permission_classes = [HasTeamContext]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(team=self.request.team).prefetch_related(
            "messages", "tags", "internal_notes"
        )


# ---------------------------------------------------------------------------
# Scale features
# ---------------------------------------------------------------------------


class TagListCreateView(generics.ListCreateAPIView):
    """List all tags or create a new one."""

    serializer_class = TagSerializer
    permission_classes = [HasTeamContext]

    def get_queryset(self):
        return Tag.objects.filter(team=self.request.team)

    def perform_create(self, serializer):
        serializer.save(team=self.request.team)


class TagDeleteView(generics.DestroyAPIView):
    """Delete a tag by ID."""

    serializer_class = TagSerializer
    permission_classes = [HasTeamContext]

    def get_queryset(self):
        return Tag.objects.filter(team=self.request.team)


class InternalNoteCreateView(APIView):
    """Create an internal note on a conversation."""

    permission_classes = [HasTeamContext]

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(pk=conversation_id, team=request.team)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InternalNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(conversation=conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CannedResponseListCreateView(generics.ListCreateAPIView):
    """List all canned responses or create a new one."""

    serializer_class = CannedResponseSerializer
    permission_classes = [HasTeamContext]

    def get_queryset(self):
        return CannedResponse.objects.filter(team=self.request.team, is_active=True)

    def perform_create(self, serializer):
        serializer.save(team=self.request.team)


class CannedResponseUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a canned response."""

    serializer_class = CannedResponseSerializer
    permission_classes = [HasTeamContext]

    def get_queryset(self):
        return CannedResponse.objects.filter(team=self.request.team)


class ConversationSearchView(APIView):
    """Full-text search across messages and conversation sender names.

    Query param: ?q=<search term>
    """

    permission_classes = [HasTeamContext]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response(
                {"error": "Search query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_query = SearchQuery(query)
        team = request.team

        # Find conversations where messages match the search query
        message_conversation_ids = (
            Message.objects.filter(conversation__team=team)
            .annotate(search=SearchVector("content"))
            .filter(search=search_query)
            .values_list("conversation_id", flat=True)
            .distinct()
        )

        # Find conversations where sender_name matches
        sender_conversation_ids = (
            Conversation.objects.filter(team=team)
            .annotate(search=SearchVector("sender_name"))
            .filter(search=search_query)
            .values_list("id", flat=True)
            .distinct()
        )

        # Combine both sets of IDs
        all_ids = set(message_conversation_ids) | set(sender_conversation_ids)

        conversations = (
            Conversation.objects.filter(team=team, id__in=all_ids)
            .prefetch_related("tags")
            .order_by("-updated_at")
        )

        serializer = ConversationSearchSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BulkActionView(APIView):
    """Perform bulk actions on conversations.

    Accepts JSON body:
        {
            "conversation_ids": ["uuid1", "uuid2"],
            "action": "resolve" | "tag",
            "tag_id": "uuid"  (required when action is "tag")
        }
    """

    permission_classes = [HasTeamContext]

    def post(self, request):
        conversation_ids = request.data.get("conversation_ids", [])
        action = request.data.get("action", "")

        if not conversation_ids:
            return Response(
                {"error": "conversation_ids is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in ("resolve", "tag"):
            return Response(
                {"error": "action must be 'resolve' or 'tag'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversations = Conversation.objects.filter(
            id__in=conversation_ids, team=request.team
        )
        matched_count = conversations.count()

        if matched_count == 0:
            return Response(
                {"error": "No matching conversations found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if action == "resolve":
            updated = conversations.update(status="resolved")
            return Response(
                {"message": f"Resolved {updated} conversation(s)."},
                status=status.HTTP_200_OK,
            )

        if action == "tag":
            tag_id = request.data.get("tag_id")
            if not tag_id:
                return Response(
                    {"error": "tag_id is required for 'tag' action."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                tag = Tag.objects.get(pk=tag_id, team=request.team)
            except Tag.DoesNotExist:
                return Response(
                    {"error": "Tag not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            created_count = 0
            for conversation in conversations:
                _, created = ConversationTag.objects.get_or_create(
                    conversation=conversation, tag=tag
                )
                if created:
                    created_count += 1

            return Response(
                {
                    "message": f"Tagged {created_count} conversation(s) with '{tag.name}'.",
                    "already_tagged": matched_count - created_count,
                },
                status=status.HTTP_200_OK,
            )


class KnowledgeBaseUploadView(APIView):
    """Upload a file (text or PDF) to the knowledge base.

    The file is chunked, embedded, and stored as KnowledgeBase entries.
    Accepts multipart form data with:
        - file: the uploaded file
        - category: one of billing, technical, account, general (default: general)
    """

    permission_classes = [HasTeamContext]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = request.data.get("category", "general")
        valid_categories = [c[0] for c in KnowledgeBase.CATEGORY_CHOICES]
        if category not in valid_categories:
            return Response(
                {"error": f"category must be one of: {', '.join(valid_categories)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract text from file
        filename = uploaded_file.name.lower()
        try:
            if filename.endswith(".pdf"):
                text = self._extract_pdf_text(uploaded_file)
            else:
                text = uploaded_file.read().decode("utf-8")
        except Exception as e:
            logger.error("Failed to read uploaded file: %s", str(e))
            return Response(
                {"error": f"Failed to read file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not text.strip():
            return Response(
                {"error": "File contains no extractable text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Chunk and embed
        chunks = chunk_text(text)
        entries_created = 0

        for chunk in chunks:
            embedding = generate_embedding(chunk)
            KnowledgeBase.objects.create(
                team=request.team,
                content=chunk,
                embedding=embedding,
                category=category,
                metadata={"source_file": uploaded_file.name},
            )
            entries_created += 1

        return Response(
            {
                "message": f"Successfully processed '{uploaded_file.name}'.",
                "chunks_created": entries_created,
                "category": category,
            },
            status=status.HTTP_201_CREATED,
        )

    def _extract_pdf_text(self, uploaded_file) -> str:
        """Extract text from a PDF file using pypdf."""
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
        return "\n\n".join(pages_text)
