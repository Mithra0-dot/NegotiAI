from app.personas.models import Constraints, PersonaInternal
from app.strategies.models import Tactic

# The hiring manager is the one paying, so their walk_away is a ceiling:
# the max base they'll approve before losing the candidate is preferable
# to blowing the budget.
PERSONA = PersonaInternal(
    scenario_id="salary-negotiation",
    role_description=(
        "Hiring manager at a mid-size fintech company, extending a base "
        "salary offer for a senior engineering role."
    ),
    goals=[
        "Close the hire without exceeding the approved compensation band",
        "Protect internal pay equity with the existing team",
    ],
    constraints=Constraints(
        target=105_000,
        walk_away=122_000,
        unit="USD/year base salary",
    ),
    # The candidate wants a higher base — target is their ideal, walk_away
    # the minimum they'd accept before declining the offer.
    user_constraints=Constraints(
        target=130_000,
        walk_away=115_000,
        unit="USD/year base salary",
    ),
    personality_traits=["deadline-driven", "friendly but firm", "risk-averse on budget"],
    opening_tactic="Anchors low citing the approved band, creates urgency around a close date",
    opening_tactic_tag=Tactic.ANCHORING,
)
