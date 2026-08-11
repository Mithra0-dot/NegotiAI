"""The actual LLM call: LangChain + Anthropic (langchain-anthropic).

No temperature override — Claude Sonnet 5 (like Opus 5) rejects a
non-default `temperature` with a 400, so reply variety comes entirely
from the system prompt's tactic/signal framing, not a sampling knob.
"""

from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.agent.prompts import build_system_prompt
from app.classifier.models import DetectedSignal
from app.config import settings
from app.personas.models import PersonaInternal
from app.schemas import ChatTurn
from app.strategies.models import Phase, Tactic


class AgentError(Exception):
    """Wraps any failure from the LangChain/Anthropic call so callers
    (main.py) don't need to know the underlying SDK's exception types —
    just that the agent couldn't produce a reply."""


@lru_cache(maxsize=1)
def get_llm() -> ChatAnthropic:
    """Cached so the client (and its connection pool) is built once, not
    per-request.

    `anthropic_api_key` is only passed when explicitly configured — the
    field is a SecretStr and rejects an explicit None, so omitting the
    kwarg entirely (rather than passing None) is what lets the
    underlying Anthropic SDK fall back to its own credential resolution
    (ANTHROPIC_AUTH_TOKEN, an `ant auth login` profile, etc.) — see
    app/config.py's docstring. No `temperature` — Claude Sonnet 5 rejects
    a non-default value, and leaving it unset means langchain-anthropic
    omits the field from the request entirely rather than sending one.
    """
    kwargs: dict[str, object] = {
        "model": settings.anthropic_model,
        "max_tokens": 300,
        "default_request_timeout": 30,
    }
    if settings.anthropic_api_key:
        kwargs["anthropic_api_key"] = settings.anthropic_api_key
    return ChatAnthropic(**kwargs)


def _to_langchain_messages(history: list[ChatTurn]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(HumanMessage(content=turn.text))
        else:
            messages.append(AIMessage(content=turn.text))
    return messages


def generate_reply(
    persona: PersonaInternal,
    phase: Phase,
    tactic: Tactic,
    detected_signals: list[DetectedSignal],
    message: str,
    history: list[ChatTurn],
) -> str:
    """Builds the system prompt + conversation history, calls Claude, and
    returns the reply text. Raises AgentError on any failure — callers
    turn that into an HTTP error rather than falling back to stub text,
    so a real failure is never mistaken for a real (if bland) reply."""
    system_prompt = build_system_prompt(persona, phase, tactic, detected_signals)
    conversation = [
        SystemMessage(content=system_prompt),
        *_to_langchain_messages(history),
        HumanMessage(content=message),
    ]

    try:
        response = get_llm().invoke(conversation)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see AgentError docstring
        raise AgentError(f"Negotiation agent call failed: {exc}") from exc

    reply = response.content
    if not isinstance(reply, str) or not reply.strip():
        raise AgentError("Negotiation agent returned an empty reply.")

    return reply
