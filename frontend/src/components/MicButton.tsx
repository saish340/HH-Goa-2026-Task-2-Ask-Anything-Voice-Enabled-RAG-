export type MicState = "idle" | "listening" | "recording" | "processing" | "done";

const BAR_DELAYS = ["0ms", "120ms", "240ms", "80ms", "200ms"];
const BAR_COLORS = [
  "var(--color-pink)",
  "var(--color-mustard)",
  "var(--color-cream)",
  "var(--color-pink)",
  "var(--color-mustard)",
];

export function MicButton({
  state,
  onClick,
}: {
  state: MicState;
  onClick: () => void;
}) {
  const spinning = state === "listening" || state === "recording" || state === "processing";
  const busy = state === "processing";

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Ask a question with your voice"
      className="relative block h-[150px] w-[150px] shrink-0 cursor-pointer sm:h-[170px] sm:w-[170px]"
    >
      {/* dashed pink ring */}
      <span
        className={`absolute -inset-[9px] rounded-full border-2 border-dashed border-[var(--color-pink)] ${
          spinning ? "animate-ring-rotate" : ""
        }`}
      />

      {/* green circle */}
      <span className="absolute inset-0 flex items-center justify-center rounded-full bg-[var(--color-forest-dark)]">
        {state === "recording" ? (
          <span className="flex h-14 items-end gap-1.5">
            {BAR_DELAYS.map((d, i) => (
              <span
                key={i}
                style={{
                  animation: "bar-bounce 700ms ease-in-out infinite",
                  animationDelay: d,
                  backgroundColor: BAR_COLORS[i],
                }}
                className="block h-12 w-1.5 origin-bottom rounded-full"
              />
            ))}
          </span>
        ) : (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="#ffffff"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`h-16 w-16 transition-opacity ${busy ? "opacity-40" : "opacity-100"}`}
            aria-hidden="true"
          >
            <rect x="9" y="2.5" width="6" height="11.5" rx="3" />
            <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0" />
            <path d="M12 18v3.5" />
            <path d="M8.5 21.5h7" />
          </svg>
        )}
      </span>

      {/* mustard badge */}
      <span className="absolute -top-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-mustard)]">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--color-forest-dark)"
          strokeWidth="2.2"
          strokeLinecap="round"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M4 8h10M18 8h2M4 16h4M12 16h8" />
          <circle cx="16" cy="8" r="2" fill="var(--color-mustard)" />
          <circle cx="10" cy="16" r="2" fill="var(--color-mustard)" />
        </svg>
      </span>

      {/* white tag */}
      <span className="absolute -bottom-2 -left-6 flex items-center gap-1.5 rounded-lg bg-white px-2.5 py-1.5 shadow-[0_4px_10px_rgba(20,36,27,0.2)]">
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true">
          <g fill="var(--color-forest)">
            <rect x="1" y="6" width="2" height="4" rx="1" />
            <rect x="5" y="3" width="2" height="10" rx="1" />
            <rect x="9" y="5" width="2" height="6" rx="1" />
            <rect x="13" y="7" width="2" height="2" rx="1" />
          </g>
        </svg>
        <span className="font-mono text-[9px] font-bold tracking-[0.12em] text-[var(--color-pink)]">
          ASK ANYTHING
        </span>
      </span>
    </button>
  );
}