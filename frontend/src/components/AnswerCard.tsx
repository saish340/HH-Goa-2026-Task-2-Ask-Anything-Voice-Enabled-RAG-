import type { AskResponse } from "@/lib/api";

// Retune against fresh /benchmarks output (fast tier: P50 ~68ms, P100 ~131ms).
const LATENCY_GOOD_MS = 100;
const LATENCY_WARN_MS = 200;
const CONFIDENCE_GOOD = 0.8;
const CONFIDENCE_WARN = 0.5;

function latencyColor(ms: number) {
  if (ms < LATENCY_GOOD_MS) return "var(--color-status-good)";
  if (ms <= LATENCY_WARN_MS) return "var(--color-status-warn)";
  return "var(--color-status-bad)";
}

function confidenceColor(c: number) {
  if (c > CONFIDENCE_GOOD) return "var(--color-status-good)";
  if (c >= CONFIDENCE_WARN) return "var(--color-status-warn)";
  return "var(--color-status-bad)";
}

function Eyebrow({ children }: { children: string }) {
  return (
    <p className="font-mono text-xs font-bold tracking-[0.22em] text-[var(--color-pink)] uppercase">
      {children}
    </p>
  );
}

export function AnswerCard({ response }: { response: AskResponse }) {
  const refusedOrError = response.status !== "ok";
  const message =
    response.status === "error" ? (response.error ?? "Something went wrong.") : response.answer;

  if (refusedOrError) {
    return (
      <section
        className="card-poster animate-fade-slide-up w-full border-2 border-[var(--color-pink)]"
        aria-live="polite"
      >
        <div className="flex items-start gap-3">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-[var(--color-pink)] font-mono text-sm font-bold text-[var(--color-pink)]">
            !
          </span>
          <div className="flex-1">
            <Eyebrow>{response.status === "error" ? "ERROR" : "REFUSED"}</Eyebrow>
            <p className="mt-3 font-mono text-[15px] leading-[1.7] text-[var(--color-ink)]">
              {message}
            </p>
          </div>
        </div>
        <div className="mt-6 border-t-2 border-[var(--color-ink)]/15 pt-4 font-mono text-xs">
          <span className="text-[var(--color-ink)]/70">Latency: </span>
          <span style={{ color: latencyColor(response.latency_ms) }} className="font-bold">
            {response.latency_ms}ms
          </span>
        </div>
      </section>
    );
  }

  return (
    <section className="card-poster animate-fade-slide-up w-full" aria-live="polite">
      <Eyebrow>ANSWER</Eyebrow>
      <p className="mt-4 font-mono text-[15px] leading-[1.7] text-[var(--color-ink)]">
        {response.answer}
      </p>

      {response.sources.length > 0 && (
        <ul className="mt-6 flex flex-wrap gap-2">
          {response.sources.map((s) => (
            <li key={s}>
              <span className="inline-block cursor-default rounded-full border-2 border-[var(--color-ink)] bg-[var(--color-cream-alt)] px-3 py-1 font-mono text-[11px] text-[var(--color-ink)] transition-all hover:-translate-y-px hover:border-[var(--color-pink)] hover:text-[var(--color-pink)]">
                {s}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-6 flex flex-wrap gap-x-8 gap-y-2 border-t-2 border-[var(--color-ink)]/15 pt-4 font-mono text-xs">
        <p>
          <span className="text-[var(--color-ink)]/70">Confidence: </span>
          <span style={{ color: confidenceColor(response.confidence) }} className="font-bold">
            {Math.round(response.confidence * 100)}%
          </span>
        </p>
        <p>
          <span className="text-[var(--color-ink)]/70">Latency: </span>
          <span style={{ color: latencyColor(response.latency_ms) }} className="font-bold">
            {response.latency_ms}ms
          </span>
        </p>
      </div>
    </section>
  );
}
