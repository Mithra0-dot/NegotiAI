import { scenarios } from "../data/scenarios";
import type { Scenario } from "../types/scenario";
import { ScenarioCard } from "./ScenarioCard";

interface ScenarioPickerProps {
  onSelect: (scenario: Scenario) => void;
}

export function ScenarioPicker({ onSelect }: ScenarioPickerProps) {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <header className="mb-10">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-100">
          Pick a scenario
        </h1>
        <p className="mt-2 text-slate-400">
          Choose who you're negotiating against. Each scenario has its own
          persona, goals, and constraints.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {scenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
