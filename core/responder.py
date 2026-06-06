import logging

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_response(
    message: str,
    conversation_history: list,
    knowledge_chunks: list,
) -> dict:
    """Generate a support response using Claude Sonnet with RAG context.

    Args:
        message: The current customer message.
        conversation_history: List of dicts with 'role' and 'content' keys.
        knowledge_chunks: List of relevant knowledge base content strings.

    Returns:
        Dict with 'response' (str) and 'confidence' (float).
    """
    from .ai_keys import get_anthropic_api_key

    client = anthropic.Anthropic(api_key=get_anthropic_api_key())

    system_prompt = """<role>
You are a polite, professional customer support assistant. You represent the company.
Use few words: short sentences, no filler, no long intros or sign-offs unless needed.
</role>

<rules>
- ONLY answer using the knowledge base context below. If it is insufficient, say so briefly
  and offer a human teammate — do not guess.
- Never invent policies, prices, guarantees, or technical details.
- Be warm and respectful. If the customer sounds upset, one short acknowledgement is enough,
  then help in minimal words.
- If the customer asks for a human, agent, person, manager, or live help in ANY wording
  (including indirect phrases like "not a bot" or "real person"), do NOT try to solve their
  issue. Reply with one or two short polite sentences confirming they will be connected to
  someone on the team. No troubleshooting first.
- When you have answered using the knowledge base and the customer's request is addressed,
  end with ONE short question asking if their issue is resolved or if they need anything else
  (e.g. "Does that solve your issue, or is there anything else you need?"). Keep it to one line.
- Prefer 1–3 short sentences total for normal answers. Avoid bullet lists unless the user asks.
</rules>"""

    # Build the user message with knowledge context
    kb_context = "\n---\n".join(knowledge_chunks) if knowledge_chunks else "No relevant knowledge base entries found."

    user_content = f"""<knowledge_base_context>
{kb_context}
</knowledge_base_context>

<customer_message>
{message}
</customer_message>"""

    # Build messages list from conversation history + current message
    messages = []
    for entry in conversation_history:
        role = "assistant" if entry["role"] == "ai" else "user"
        messages.append({"role": role, "content": entry["content"]})
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.messages.create(
            model=settings.CLAUDE_SONNET_MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )

        response_text = response.content[0].text.strip()
        stop_reason = response.stop_reason

        # Heuristic confidence: lower if the model hedged or offered handoff
        confidence = 0.9
        hedge_phrases = [
            "i'm not sure",
            "i don't have enough information",
            "connect you with",
            "human agent",
            "i cannot confirm",
        ]
        for phrase in hedge_phrases:
            if phrase in response_text.lower():
                confidence = 0.5
                break

        if stop_reason != "end_turn":
            confidence = max(confidence - 0.2, 0.1)

        return {
            "response": response_text,
            "confidence": confidence,
        }

    except Exception as e:
        logger.error("Responder error: %s", str(e))
        return {
            "response": (
                "Sorry — something went wrong on our side. "
                "I'm connecting you with a teammate who can help."
            ),
            "confidence": 0.0,
        }
