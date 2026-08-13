import type { StrategyVariant } from "./chat";

/**
 * Static display shape for the opponent-preset picker — same "mirrors a
 * future API response" convention as types/scenario.ts's Scenario.
 */
export interface OpponentPreset {
  variant: StrategyVariant;
  label: string;
  /** 1-2 line description of how this preset actually negotiates —
   * kept accurate to the real backend behavior (see
   * app/strategies/default.py / app/strategies/hardline.py), not just a
   * name swap. */
  description: string;
}
