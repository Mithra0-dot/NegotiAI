"""Generates the simulated user's next message — the LLM-role-play half
of a synthetic session. Mirrors app/agent/llm.py's structure (mock
branch, cached ChatAnthropic client, LangChain message construction) but
plays the opposite seat: where app/agent builds a prompt for the
negotiation *opponent*, this builds one for the human *user*'s side,
using PersonaInternal.user_constraints (see app/personas/models.py) as
their private position and eval/user_types.py's UserType as their
behavioral style.

Reuses app.agent.llm.get_llm() rather than constructing a second
ChatAnthropic client — same cached connection pool, same API-key
resolution, one source of truth for the Anthropic wiring.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.agent import AgentError
from app.agent.llm import get_llm
from app.config import settings
from app.personas.models import PersonaInternal
from app.schemas import ChatTurn
from eval.mock_user import generate_mock_user_message
from eval.user_types import BEHAVIOR_INSTRUCTIONS, UserType


def build_user_system_prompt(persona: PersonaInternal, user_type: UserType) -> str:
    """Builds the system prompt for one simulated-user turn.

    Uses persona.user_constraints (the human side's own target/walk-away
    — see PersonaInternal's docstring: no leak concern here, it's the
    user's own info) and persona.role_description, which every scenario
    file already writes in second person ("negotiating *your* hourly
    rate...") — enough context to place the simulated user correctly
    without a dedicated per-scenario field.
    """
    lines = [
        "You are role-playing as the human side of a negotiation "
        "training simulation — the counterpart to the opposing party "
        "described below.",
        "Stay fully in character — natural, realistic negotiation "
        "dialogue only. No meta-commentary about \"simulations,\" "
        "\"user types,\" or being an AI. Keep replies concise (2-4 "
        "sentences), like a real conversational negotiation message.",
        "",
        f"Who you're negotiating with: {persona.role_description}",
        f"Your negotiating style: {BEHAVIOR_INSTRUCTIONS[user_type]}",
        "",
        "Your private negotiating position (this is what you're "
        "actually trying to get — reveal it strategically through "
        "dialogue as your style dictates, never as a flat data dump):",
        f"- Your ideal outcome: {persona.user_constraints.target} {persona.user_constraints.unit}",
        f"- Your walk-away point: {persona.user_constraints.walk_away} {persona.user_constraints.unit}",
        "",
        # Session-end detection (app/scoring/outcome_detection.py) looks
        # for specific decisive phrasing. A free-form "sounds good" isn't
        # reliably caught, so the close itself needs an explicit, exact
        # phrase — same trick a real person's natural wording gets away
        # with implicitly, made explicit here so simulated sessions
        # actually conclude instead of always hitting the turn limit.
        "When you decide to conclude the negotiation: if you're "
        "accepting the current terms, your message must include the "
        "exact phrase \"I accept your offer\". If you're ending things "
        "without a deal, your message must include the exact phrase "
        "\"I'm walking away\". Only use one of these when you're "
        "genuinely ready to end the negotiation — not before.",
    ]
    return "\n".join(lines)


def _to_langchain_messages_for_user(history: list[ChatTurn]) -> list[BaseMessage]:
    """Mirrors app/agent/llm.py's _to_langchain_messages, but roles are
    inverted: from the simulated user's point of view, the agent's
    replies (ChatTurn.role == "assistant") are what they're responding
    to (HumanMessage), and their own prior turns (role == "user") are
    their own past output (AIMessage)."""
    messages: list[BaseMessage] = []
    for turn in history:
        if turn.role == "assistant":
            messages.append(HumanMessage(content=turn.text))
        else:
            messages.append(AIMessage(content=turn.text))
    return messages


def generate_user_message(
    persona: PersonaInternal,
    user_type: UserType,
    turn_number: int,
    history: list[ChatTurn],
) -> str:
    """Generates the simulated user's next message. Raises AgentError
    (same type app/agent/llm.py raises) on any LLM failure — the
    simulation batch lets that propagate rather than recording a
    half-formed session (see eval/run_simulation.py)."""
    if settings.mock_llm:
        return generate_mock_user_message(persona, user_type, turn_number)

    system_prompt = build_user_system_prompt(persona, user_type)
    conversation: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    if history:
        conversation += _to_langchain_messages_for_user(history)
    else:
        # Turn 1: no prior turns to seed the API's required user-first
        # message shape — an explicit kickoff instruction stands in for
        # it, same purpose as history's first HumanMessage on later
        # turns, just synthetic since there's nothing real to send yet.
        conversation.append(
            HumanMessage(content="Begin the negotiation with your opening message now.")
        )

    try:
        response = get_llm().invoke(conversation)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see AgentError docstring
        raise AgentError(f"Simulated user call failed: {exc}") from exc

    reply = response.content
    if not isinstance(reply, str) or not reply.strip():
        raise AgentError("Simulated user returned an empty message.")

    return reply
