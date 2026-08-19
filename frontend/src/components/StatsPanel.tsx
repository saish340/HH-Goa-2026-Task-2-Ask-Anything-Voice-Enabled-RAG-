import { useEffect, useState } from "react";
import { benchmarks, type BenchmarksResponse } from "@/lib/api";

// Backend reports benchmark values as already-scaled percent numbers (84, 93.42)
// and fractions only for mrr (0.576), so we render percentages as-is.
function pct(v?: number) {
  return v === undefined ? "—" : `${Math.round(v)}%`;
}
function ms(v?: number) {
  return v === undefined ? "—" : `${v}ms`;
}

export function StatsPanel() {
  const [data, setData] = useState<BenchmarksResponse | null>(null);

  useEffect(() => {
    let alive = true;
    benchmarks().then((d) => alive && setData(d));
    return () => {
      alive = false;
    };
  }, []);

  const rows: Array<[string, string]> = data?.available
    ? [
        ["P50 latency", ms(data.p50)],
        ["P70 latency", ms(data.p70)],
        ["P100 latency", ms(data.p100)],
        ["Recall@5", pct(data.recall_at_5)],
        ["Recall@10", pct(data.recall_at_10)],
        ["MRR", data.mrr?.toFixed(2) ?? "—"],
        ["Grounded rate", pct(data.grounded_rate)],
        ["Refusal rate", pct(data.refusal_rate)],
        ["Overall accuracy", pct(data.overall_accuracy)],
      ]
    : [];

  return (
    <section className="card-poster w-full">
      <p className="font-mono text-xs font-bold tracking-[0.22em] text-[var(--color-pink)] uppercase">
        BENCHMARKS
      </p>
      {!data ? (
        <p className="mt-4 font-mono text-xs text-[var(--color-ink)]/60">Loading…</p>
      ) : !data.available ? (
        <p className="mt-4 font-mono text-xs text-[var(--color-ink)]/70">Not yet benchmarked</p>
      ) : (
        <dl className="mt-5 grid grid-cols-1 gap-x-10 gap-y-2 sm:grid-cols-2">
          {rows.map(([k, v]) => (
            <div
              key={k}
              className="flex items-baseline justify-between gap-4 border-b border-dashed border-[var(--color-ink)]/20 pb-1.5"
            >
              <dt className="font-mono text-[11px] text-[var(--color-ink)]/70">{k}</dt>
              <dd className="font-mono text-[12px] font-bold text-[var(--color-ink)]">{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
