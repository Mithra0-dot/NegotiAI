"""Maps each StrategyVariant to its select_tactic() implementation.

The one place that needs to know both variants exist — app/chat_pipeline.py
dispatches through this dict instead of importing a specific variant's
select_tactic directly, so adding a third variant later is a one-line
addition here plus a new module, never a change to chat_pipeline.py,
default.py, or main.py (see default.py's module docstring).
"""

from collections.abc import Callable

from app.classifier.models import DetectedSignal
from app.personas.models import PersonaInternal
from app.strategies import default, hardline
from app.strategies.models import Phase, StrategyVariant, Tactic

SelectTacticFn = Callable[[PersonaInternal, Phase, list[DetectedSignal]], Tactic]

SELECT_TACTIC_BY_VARIANT: dict[StrategyVariant, SelectTacticFn] = {
    StrategyVariant.DEFAULT: default.select_tactic,
    StrategyVariant.HARDLINE: hardline.select_tactic,
}
