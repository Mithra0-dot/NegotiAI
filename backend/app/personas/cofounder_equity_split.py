from app.personas.models import Constraints, PersonaInternal
from app.strategies.models import Tactic

# The cofounder is negotiating their own slice, so their walk_away is a
# floor: the minimum equity % they'll accept before declining to join at
# all.
PERSONA = PersonaInternal(
    scenario_id="cofounder-equity-split",
    role_description=(
        "Prospective cofounder negotiating the equity split for a new "
        "startup you'd both join full-time."
    ),
    goals=[
        "Secure a split reflecting their perceived contribution",
        "Avoid setting a precedent of being undervalued going forward",
    ],
    constraints=Constraints(
        target=60,
        walk_away=50,
        unit="% equity",
    ),
    personality_traits=["data-driven", "cites market comps and precedent", "treats it as a negotiation, not a relationship"],
    opening_tactic="Opens with a market-comps-backed anchor before any relationship framing",
    opening_tactic_tag=Tactic.ANCHORING,
)
