import { opponentPresets } from "../data/opponentPresets";
import type { StrategyVariant } from "../types/chat";

interface OpponentPresetPickerProps {
  onSelect: (variant: StrategyVariant) => void;
}

// Card + grid in one file, unlike ScenarioCard/ScenarioPicker's split —
// with only 2 presets there's no reuse benefit to separating them, and
// splitting would just be an extra file for its own sake.
export function OpponentPresetPicker({ onSelect }: OpponentPresetPickerProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-100">
        Choose your opponent
      </h2>
      <p className="mt-1 text-sm text-slate-400">
        Pick a negotiating style to play against.
      </p>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {opponentPresets.map((preset) => (
          <button
            key={preset.variant}
            type="button"
            onClick={() => onSelect(preset.variant)}
            className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-900/60 p-5 text-left transition hover:-translate-y-0.5 hover:border-violet-500/50 hover:bg-slate-900 hover:shadow-lg hover:shadow-violet-950/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
          >
            <h3 className="text-base font-semibold text-slate-100">
              {preset.label}
            </h3>
            <p className="text-sm leading-relaxed text-slate-400">
              {preset.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
