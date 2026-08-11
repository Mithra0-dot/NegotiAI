import type { SignalType } from "../types/chat";

const LABELS: Record<SignalType, string> = {
  unforced_concession: "Unforced concession",
  hedging: "Hedging language",
  urgency: "Urgency/anxiety",
  premature_agreement: "Premature agreement",
};

// A fresh 4-color set, distinct from DifficultyBadge's emerald/amber/rose
// so these don't read as difficulty levels.
const STYLES: Record<SignalType, string> = {
  unforced_concession: "bg-fuchsia-500/15 text-fuchsia-400 ring-fuchsia-500/30",
  hedging: "bg-sky-500/15 text-sky-400 ring-sky-500/30",
  urgency: "bg-rose-500/15 text-rose-400 ring-rose-500/30",
  premature_agreement: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
};

export function SignalTag({ signalType }: { signalType: SignalType }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${STYLES[signalType]}`}
    >
      {LABELS[signalType]}
    </span>
  );
}
