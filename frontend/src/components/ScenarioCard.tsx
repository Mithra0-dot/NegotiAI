import type { Scenario } from "../types/scenario";
import { DifficultyBadge } from "./DifficultyBadge";

interface ScenarioCardProps {
  scenario: Scenario;
  onSelect: (scenario: Scenario) => void;
}

export function ScenarioCard({ scenario, onSelect }: ScenarioCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(scenario)}
      className="group flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-5 text-left transition hover:-translate-y-0.5 hover:border-violet-500/50 hover:bg-slate-900 hover:shadow-lg hover:shadow-violet-950/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold text-slate-100">
          {scenario.name}
        </h3>
        <DifficultyBadge difficulty={scenario.difficulty} />
      </div>

      <p className="text-sm leading-relaxed text-slate-400">
        {scenario.blurb}
      </p>

      <p className="mt-auto pt-2 text-xs text-slate-500">
        <span className="text-slate-600">Opponent: </span>
        {scenario.opponentStyleHint}
      </p>
    </button>
  );
}
