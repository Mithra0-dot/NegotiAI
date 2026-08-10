from app.personas.apartment_lease import PERSONA as APARTMENT_LEASE
from app.personas.cofounder_equity_split import PERSONA as COFOUNDER_EQUITY_SPLIT
from app.personas.freelance_rate import PERSONA as FREELANCE_RATE
from app.personas.models import PersonaInternal
from app.personas.salary_negotiation import PERSONA as SALARY_NEGOTIATION

PERSONAS: dict[str, PersonaInternal] = {
    persona.scenario_id: persona
    for persona in (
        SALARY_NEGOTIATION,
        FREELANCE_RATE,
        APARTMENT_LEASE,
        COFOUNDER_EQUITY_SPLIT,
    )
}


def get_persona(scenario_id: str) -> PersonaInternal | None:
    """Look up the full (backend-only) persona config by scenario ID, or
    None if unknown. Callers must send `.to_public()` to the client, never
    this directly — see PersonaInternal's docstring."""
    return PERSONAS.get(scenario_id)
