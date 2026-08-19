export type Stage =
  | "idle"
  | "listening..."
  | "transcribing..."
  | "retrieving..."
  | "generating..."
  | "done";

export function StatusLine({ stage }: { stage: Stage }) {
  if (stage === "idle") return <div className="h-9" aria-hidden="true" />;
  return (
    <div className="flex h-9 items-center justify-center">
      <span
        key={stage}
        className="animate-fade-slide-up inline-block rounded-full border-2 border-[var(--color-pink)] bg-[var(--color-pink-soft)] px-4 py-1.5 font-mono text-[11px] font-bold tracking-[0.16em] text-[var(--color-pink)] uppercase"
        aria-live="polite"
      >
        {stage}
      </span>
    </div>
  );
}