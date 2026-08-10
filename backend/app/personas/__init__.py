from app.personas.apartment_lease import PERSONA as APARTMENT_LEASE
from app.personas.cofounder_equity_split import PERSONA as COFOUNDER_EQUITY_SPLIT
from app.personas.freelance_rate import PERSONA as FREELANCE_RATE
from app.personas.models import PersonaConfig
from app.personas.salary_negotiation import PERSONA as SALARY_NEGOTIATION

PERSONAS: dict[str, PersonaConfig] = {
    persona.scenario_id: persona
    for persona in (
        SALARY_NEGOTIATION,
        FREELANCE_RATE,
        APARTMENT_LEASE,
        COFOUNDER_EQUITY_SPLIT,
    )
}


def get_persona(scenario_id: str) -> PersonaConfig | None:
    """Look up a persona config by scenario ID, or None if unknown."""
    return PERSONAS.get(scenario_id)
