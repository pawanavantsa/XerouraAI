import logging
import re

logger = logging.getLogger(__name__)

# Short, polite reply when escalating to a human (used by API paths).
DEFAULT_HANDOFF_REPLY = "Thank you — I'm connecting you with a teammate now."

# After the customer confirms their issue is resolved (used by API paths).
DEFAULT_RESOLVED_CLOSING_REPLY = (
    "Glad that helped. Message us anytime you need support."
)

# Substring matches (message lowercased). Keep multi-word, unambiguous phrases.
HUMAN_REQUEST_PHRASES = [
    "connect me to a human",
    "connect me to an agent",
    "connect me to someone",
    "connect to a human",
    "connect to human",
    "transfer me to",
    "transfer to a human",
    "transfer to agent",
    "transfer to an agent",
    "escalate to",
    "speak to a human",
    "speak to an agent",
    "speak to a person",
    "speak to human",
    "speak with a human",
    "speak with an agent",
    "talk to a human",
    "talk to human",
    "talk to an agent",
    "talk to agent",
    "talk to a person",
    "talk to someone",
    "talk with a human",
    "chat with a human",
    "chat with an agent",
    "real person",
    "real human",
    "live agent",
    "live human",
    "live person",
    "live representative",
    "human agent",
    "human operator",
    "human please",
    "agent please",
    "customer service representative",
    "i need human",
    "i need a human",
    "i need an agent",
    "i need a agent",
    "need a human",
    "need human",
    "need an agent",
    "i want a human",
    "i want human",
    "i want an agent",
    "want a human",
    "want to talk to a human",
    "want to speak to a human",
    "get me a human",
    "get me an agent",
    "give me a human",
    "give me an agent",
    "give me human",
    "let me talk to a human",
    "let me speak to",
    "speak to manager",
    "talk to a manager",
    "talk to manager",
    "speak with a manager",
    "speak to a manager",
    "real agent",
    "actual person",
    "someone real",
    "not a bot",
    "not a robot",
    "stop the bot",
    "human being",
    "can i get a human",
    "could i get a human",
    "may i speak to a human",
    "can i have a human",
]

# Customer clearly does NOT want a human — do not escalate.
_DECLINES_HUMAN_RE = re.compile(
    r"(?ix)\b(i|we)\s+(don'?t|do\s+not)\s+(want|need)\s+(a\s+|an\s+|the\s+|to\s+talk\s+to\s+|to\s+speak\s+to\s+)?(a\s+|an\s+)?(human|agent|person|representative|operator)\b"
)

# Broad intent: ask for a human, agent, or live person in natural language.
_HUMAN_INTENT_RE = re.compile(
    r"""(?ix)
    \b(?:connect|transfer|escalate|patch|route)\s+(?:me\s+)?(?:to\s+)?(?:a\s+|an\s+|the\s+)?
        (?:human|agent|operator|representative|manager|person|people|somebody|someone)\b
    |
    \b(?:i|we)\s+(?:really\s+|just\s+)?(?:need|want|would\s+like|wanna)\s+(?:to\s+)?
        (?:speak|talk|connect)\s+(?:to|with)\s+(?:a\s+|an\s+|the\s+)?
        (?:human|agent|person|manager|representative|operator|someone\s+real|live\s+person|real\s+person)\b
    |
    \b(?:i|we)\s+(?:need|want)\s+(?:a\s+|an\s+|the\s+)?
        (?:human|agent|live\s+agent|real\s+person|manager|representative|operator)\b
    |
    \b(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+|the\s+)?
        (?:human|agent|person|manager|representative|operator|live|real|someone|somebody)\b
    |
    \b(?:let\s+me|get\s+me|give\s+me)\s+(?:a\s+|an\s+)?
        (?:human|agent|person|manager|representative|operator|somebody)\b
    |
    \b(?:can|could|may)\s+i\s+(?:please\s+)?(?:get|have)\s+(?:a\s+|an\s+)?
        (?:human|agent|person|manager|representative|operator)\b
    |
    \b(?:can|could|may)\s+i\s+(?:please\s+)?(?:speak|talk)\s+(?:to|with)\s+(?:a\s+|an\s+)?
        (?:human|agent|person|manager|someone|somebody|operator|representative)\b
    |
    \b(?:is\s+there|are\s+there)\s+(?:a\s+|an\s+|any\s+)?
        (?:human|agent|person|real\s+person|live\s+person)\b
    |
    \b(?:get|put)\s+me\s+(?:through\s+)?(?:to\s+)?(?:a\s+|an\s+)?
        (?:human|agent|person|manager)\b
    |
    \bhuman\s+representative\b
    |
    \blive\s+(?:chat\s+)?(?:with\s+)?(?:a\s+|an\s+)?
        (?:human|agent|representative|person)\b
    """,
)


def _customer_declines_human(message_lower: str) -> bool:
    return bool(_DECLINES_HUMAN_RE.search(message_lower))


# Phrases indicating the *assistant* (previous turn or current draft) offered human/teammate help.
_HANDOFF_OFFER_MARKERS = (
    "connect you with",
    "connecting you with",
    "connect you to",
    "get you connected",
    "i'll get you connected",
    "ill get you connected",
    "someone on our team",
    "someone from our team",
    "teammate",
    "team member",
    "human agent",
    "live agent",
    "speak with someone",
    "talk to someone on",
    "would that work for you",
    "happy to connect you",
    "i'd be happy to connect",
    "id be happy to connect",
    "put you in touch",
    "reach a team member",
)

# Short replies accepting a handoff offer (previous AI message must match _HANDOFF_OFFER_MARKERS).
_AFFIRMATIVE_HANDOFF_RE = re.compile(
    r"(?ix)^\s*("
    r"yes|yeah|yep|yup|sure|ok|okay|please|please do|"
    r"sounds good|that works|that'd work|that would work|"
    r"thank you|thanks|ty|thx"
    r")[\s!.]*$"
)


def ai_message_offers_handoff(text: str) -> bool:
    """True if assistant text offers connecting the customer to a human/teammate."""
    if not (text or "").strip():
        return False
    lower = text.lower()
    return any(m in lower for m in _HANDOFF_OFFER_MARKERS)


def assistant_response_offers_handoff(text: str) -> bool:
    """Same as ai_message_offers_handoff; use when checking the model's outgoing reply."""
    return ai_message_offers_handoff(text)


def _is_affirmative_handoff_reply(message: str) -> bool:
    return bool(_AFFIRMATIVE_HANDOFF_RE.match((message or "").strip()))


# Previous AI asked whether the *main issue* is fixed (customer "no" = still broken → escalate).
_ISSUE_FIXED_ASK_MARKERS = (
    "did that solve",
    "does that solve",
    "is your issue resolved",
    "is everything working",
    "all set now",
    "still having this issue",
    "still having trouble",
    "does that help",
)

# Previous AI asked whether they need *more help* (customer "no" = nothing else → close ticket).
_ADDITIONAL_HELP_ASK_MARKERS = (
    "anything else you need",
    "anything else we can",
    "anything else i can",
    "is there anything else",
    "need anything else",
    "help with anything else",
    "something else you need",
    "anything else?",
    "need help with anything else",
)

_RESOLUTION_CONFIRM_RE = re.compile(
    r"(?ix)^\s*("
    r"yes|yeah|yep|yup|sure|ok|okay|"
    r"all good|all set|we'?re good|i'?m good|"
    r"that worked|that helped|it works|working now|fixed|solved|"
    r"thank you|thanks|ty|thx|perfect|great|awesome"
    r")[\s!.]*$"
)

# Customer declines *further* help ("anything else?") — conversation complete.
_ADDITIONAL_HELP_DECLINE_RE = re.compile(
    r"(?ix)^\s*("
    r"no|nope|nah|"
    r"no thanks|no thank you|"
    r"that'?s all|nothing else|"
    r"i'?m good|i am good|all good|we'?re good|we are good"
    r")[\s!.]*$"
)

# Customer says the product/issue still doesn't work (always escalate in follow-up flow).
_ISSUE_STILL_BROKEN_RE = re.compile(
    r"(?ix)\b("
    r"not really|not yet|still not|"
    r"doesn'?t work|didn'?t work|don'?t work|"
    r"still broken|same problem|same issue|not fixed|still an issue|"
    r"still having|not working"
    r")\b"
)

# Bare no/nope to "did that solve?" (issue-only question) = not fixed.
_BARE_NO_RE = re.compile(r"(?ix)^\s*(no|nope|nah)[!. ]*$")


def ai_message_asks_issue_fixed_question(text: str) -> bool:
    """True if the assistant asked whether the original issue is solved / working."""
    if not (text or "").strip():
        return False
    lower = text.lower()
    return any(m in lower for m in _ISSUE_FIXED_ASK_MARKERS)


def ai_message_asks_additional_help_question(text: str) -> bool:
    """True if the assistant asked whether the customer needs anything else."""
    if not (text or "").strip():
        return False
    lower = text.lower()
    return any(m in lower for m in _ADDITIONAL_HELP_ASK_MARKERS)


def ai_message_asks_resolution_followup(text: str) -> bool:
    """True if the last assistant message was a resolution / follow-up question."""
    return ai_message_asks_issue_fixed_question(text) or ai_message_asks_additional_help_question(
        text
    )


def user_confirms_issue_resolved(message: str) -> bool:
    return bool(_RESOLUTION_CONFIRM_RE.match((message or "").strip()))


def user_means_no_further_help(message: str) -> bool:
    """Customer says they do not need anything else (answers no to 'anything else?')."""
    return bool(_ADDITIONAL_HELP_DECLINE_RE.match((message or "").strip()))


def user_indicates_issue_still_broken(
    message: str,
    *,
    issue_asks: bool,
    more_help: bool,
) -> bool:
    """Escalate: explicit 'still broken' language, or bare 'no' only to an issue-fixed question."""
    msg = (message or "").strip()
    if not msg:
        return False
    if _ISSUE_STILL_BROKEN_RE.search(msg):
        return True
    if issue_asks and not more_help and _BARE_NO_RE.match(msg):
        return True
    return False


def last_ai_message_before_latest_customer(conversation) -> str | None:
    """Public alias for tests and callers."""
    return _last_ai_message_text_before_latest_customer(conversation)


def _last_ai_message_text_before_latest_customer(conversation) -> str | None:
    """Latest customer message must be last in thread; return preceding AI content if any."""
    from core.models import Message

    rows = list(
        Message.objects.filter(conversation=conversation)
        .order_by("-created_at")[:8]
    )
    if len(rows) < 2:
        return None
    if rows[0].role != "customer":
        return None
    for m in rows[1:]:
        if m.role == "ai":
            return m.content
    return None


def should_escalate(
    message: str,
    classification: dict,
    conversation=None,
) -> dict:
    """Determine whether a customer message should be escalated to a human agent.

    Escalates when the customer asks for a human, agent, or live person in
    virtually any common phrasing. Does not escalate on low confidence alone.

    Args:
        message: The customer's message text.
        classification: Reserved for future use (e.g. model-based routing).

    Returns:
        A dict with ``should_escalate`` (bool), ``reason`` (str), and
        ``details`` (str).
    """
    message_lower = message.lower().strip()

    if _customer_declines_human(message_lower):
        return {
            "should_escalate": False,
            "reason": "",
            "details": "",
        }

    # Customer said yes / thanks after the AI offered a teammate — escalate for real.
    if conversation is not None and getattr(conversation, "status", None) != "escalated":
        prev_ai = _last_ai_message_text_before_latest_customer(conversation)
        if prev_ai and ai_message_offers_handoff(prev_ai) and _is_affirmative_handoff_reply(
            message
        ):
            logger.info(
                "Escalation triggered: affirmative reply after AI handoff offer: %s",
                message[:80],
            )
            return {
                "should_escalate": True,
                "reason": "customer_request",
                "details": (
                    "Customer affirmed (e.g. yes/thanks) after the assistant offered to connect "
                    "them with a teammate."
                ),
            }

    for phrase in HUMAN_REQUEST_PHRASES:
        if phrase in message_lower:
            logger.info(
                "Escalation triggered: human request phrase %r in message: %s",
                phrase,
                message[:80],
            )
            return {
                "should_escalate": True,
                "reason": "customer_request",
                "details": f"Customer explicitly requested a human agent (matched phrase: {phrase!r}).",
            }

    if _HUMAN_INTENT_RE.search(message):
        logger.info(
            "Escalation triggered: human-intent pattern in message: %s",
            message[:80],
        )
        return {
            "should_escalate": True,
            "reason": "customer_request",
            "details": "Customer message matched human-handoff intent (regex).",
        }

    return {
        "should_escalate": False,
        "reason": "",
        "details": "",
    }
