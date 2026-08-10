from app.personas.models import Constraints, PersonaInternal

# The client is the one paying, so their walk_away is a ceiling: the max
# hourly rate they'll accept before looking for a cheaper freelancer.
PERSONA = PersonaInternal(
    scenario_id="freelance-rate",
    role_description=(
        "Long-time freelance client (small business owner) negotiating "
        "your hourly rate for repeat work."
    ),
    goals=[
        "Keep the working relationship informal and low-friction",
        "Minimize the rate increase to protect their own margins",
    ],
    constraints=Constraints(
        target=65,
        walk_away=85,
        unit="USD/hour",
    ),
    personality_traits=["warm", "conflict-avoidant", "leans on loyalty and rapport"],
    opening_tactic="Leads with appreciation and relationship history before asking for a discount",
)
