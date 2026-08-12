interface OutcomeRangeBarProps {
  target: number;
  walkAway: number;
  finalValue: number | null;
  unit: string;
}

// Plain SVG/CSS rather than Recharts — a single range + one marker doesn't
// need a charting library; Recharts has no native "range + marker"
// primitive and forcing it through ReferenceLine/ReferenceArea would be
// more code for a worse result.
export function OutcomeRangeBar({
  target,
  walkAway,
  finalValue,
  unit,
}: OutcomeRangeBarProps) {
  // Higher-is-better if target > walk_away (e.g. salary), lower-is-better
  // otherwise (e.g. rent) — same direction rule scorer.py already uses.
  const higherIsBetter = target > walkAway;
  const low = Math.min(target, walkAway);
  const high = Math.max(target, walkAway);

  // Extend the visible domain to fit finalValue if it lands outside the
  // target/walk-away band (better than target, or worse than walk-away),
  // with a little padding so a marker at the very edge isn't clipped.
  const span = high - low || 1;
  const padding = span * 0.15;
  const domainLow = Math.min(low, finalValue ?? low) - padding;
  const domainHigh = Math.max(high, finalValue ?? high) + padding;
  const domainSpan = domainHigh - domainLow || 1;

  const percent = (value: number) =>
    ((value - domainLow) / domainSpan) * 100;

  const withinRange =
    finalValue !== null &&
    (higherIsBetter ? finalValue >= walkAway : finalValue <= walkAway);

  const formatValue = (value: number) =>
    unit.startsWith("%") || unit.includes("equity")
      ? `${value}${unit.replace("%", "").trim() ? ` ${unit}` : "%"}`
      : `${value.toLocaleString()} ${unit}`;

  return (
    <div>
      <div className="relative h-2 rounded-full bg-slate-800">
        {/* Favorable zone: from walk-away toward target (and beyond, since
            past target is still favorable/better) — spans right-to-100%
            when higher is better, or 0-to-walkAway when lower is better. */}
        <div
          className="absolute inset-y-0 rounded-full bg-emerald-500/20"
          style={
            higherIsBetter
              ? { left: `${percent(walkAway)}%`, right: 0 }
              : { left: 0, width: `${percent(walkAway)}%` }
          }
        />
        {finalValue !== null && (
          <div
            className={`absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-slate-950 ${
              withinRange ? "bg-emerald-400" : "bg-rose-400"
            }`}
            style={{ left: `${Math.min(100, Math.max(0, percent(finalValue)))}%` }}
          />
        )}
      </div>

      <div className="mt-2 flex justify-between text-xs text-slate-500">
        <span>
          Walk-away: <span className="text-slate-300">{formatValue(walkAway)}</span>
        </span>
        <span>
          Target: <span className="text-slate-300">{formatValue(target)}</span>
        </span>
      </div>

      {finalValue !== null ? (
        <p
          className={`mt-1 text-xs ${withinRange ? "text-emerald-400" : "text-rose-400"}`}
        >
          Final outcome: {formatValue(finalValue)}
        </p>
      ) : (
        <p className="mt-1 text-xs text-slate-600">
          No outcome value detected in the transcript.
        </p>
      )}
    </div>
  );
}
