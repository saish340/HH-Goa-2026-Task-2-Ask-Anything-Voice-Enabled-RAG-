const STAGES = [
  { label: "STAGE 01 — LISTEN", sub: "voice captured, live waveform" },
  { label: "STAGE 02 — TRANSCRIBE", sub: "speech to text, en-IN" },
  { label: "STAGE 03 — RETRIEVE", sub: "hybrid search, re-ranked" },
  { label: "STAGE 04 — GENERATE", sub: "grounded, guarded, cited" },
];

const ROTATIONS = ["-2deg", "2deg", "-1.5deg", "1.5deg"];

export function HangingCards() {
  return (
    <section aria-label="How it works" className="w-full">
      {/* bamboo pole */}
      <div className="relative h-5 w-full rounded-full border-2 border-[var(--color-ink)] bg-[var(--color-mustard)]">
        <div className="absolute inset-x-3 top-1.5 h-px bg-[var(--color-ink)]/25" />
        <div className="absolute inset-x-3 bottom-1.5 h-px bg-[var(--color-ink)]/25" />
        <div className="absolute inset-y-0 left-1/4 w-0.5 bg-[var(--color-ink)]/30" />
        <div className="absolute inset-y-0 left-1/2 w-0.5 bg-[var(--color-ink)]/30" />
        <div className="absolute inset-y-0 left-3/4 w-0.5 bg-[var(--color-ink)]/30" />
      </div>

      <ul className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-4">
        {STAGES.map((s, i) => (
          <li key={s.label} className="flex flex-col items-center">
            {/* rope */}
            <div className="flex flex-col items-center">
              <span className="h-2 w-2 rounded-full border-2 border-[var(--color-ink)] bg-[#C9A227]" />
              <span className="h-8 w-0.5 bg-[#A9762F]" />
              <span className="h-2 w-2 rounded-full border-2 border-[var(--color-ink)] bg-[#C9A227]" />
            </div>
            <div
              style={{ transform: `rotate(${ROTATIONS[i]})` }}
              className={`w-full rounded-lg border-2 border-[var(--color-ink)] p-1.5 transition-transform duration-200 hover:-translate-y-1 hover:rotate-0 ${
                i % 2 === 0 ? "bg-[var(--color-mustard)]" : "bg-[var(--color-pink)]"
              }`}
            >
              <div className="rounded-md border-2 border-white px-3 py-5 text-center">
                <p
                  className={`font-mono text-[11px] font-bold tracking-[0.1em] ${
                    i % 2 === 0 ? "text-[var(--color-forest)]" : "text-white"
                  }`}
                >
                  {s.label}
                </p>
                <p
                  className={`mt-3 font-mono text-[10px] ${
                    i % 2 === 0 ? "text-[var(--color-forest)]/80" : "text-white/85"
                  }`}
                >
                  {s.sub}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}