import type { OpponentPreset } from "../types/opponentPreset";

/**
 * The two opponent presets, presented to the user as difficulty/style
 * choices rather than the internal StrategyVariant values they map to
 * (see app/strategies/models.py's StrategyVariant + app/strategies/
 * registry.py on the backend). Static config, same pattern as
 * data/scenarios.ts.
 */
export const opponentPresets: OpponentPreset[] = [
  {
    variant: "default",
    label: "Standard",
    description:
      "Adapts as you negotiate — applies pressure if you concede too " +
      "easily, but eases into a more collaborative tone if you hold " +
      "your ground.",
  },
  {
    variant: "hardline",
    label: "Tough Negotiator",
    description:
      "Stays firm from start to finish. Applies constant pressure and " +
      "rarely eases off, even if you hold your ground — a harder opponent.",
  },
];
