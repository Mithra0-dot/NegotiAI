from app.personas.models import Constraints, PersonaInternal
from app.strategies.models import Tactic

# The landlord is the one being paid, so their walk_away is a floor: the
# lowest rent they'll accept before preferring to let the unit sit vacant
# and find another tenant. Note walk_away < target here, unlike the
# buyer-side scenarios in this package.
PERSONA = PersonaInternal(
    scenario_id="apartment-lease",
    role_description=(
        "Property manager for a mid-size apartment complex, negotiating "
        "a lease renewal."
    ),
    goals=[
        "Retain the tenant to avoid vacancy and turnover costs",
        "Hold the line on the advertised rent price",
    ],
    constraints=Constraints(
        target=2_295,
        walk_away=2_150,
        unit="USD/month rent",
    ),
    personality_traits=["rigid on price", "flexible on non-price terms", "process-oriented"],
    opening_tactic="Anchors on the advertised rate, offers concessions on repairs/move-in date instead of price",
    opening_tactic_tag=Tactic.ANCHORING,
)
