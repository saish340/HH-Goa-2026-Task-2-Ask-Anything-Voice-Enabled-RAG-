export function Wordmark() {
  return (
    <div className="relative inline-block">
      <h1
        className="font-display leading-[0.9] font-black tracking-[-0.02em] text-[var(--color-mustard)]"
        style={{
          fontSize: "clamp(2.6rem, 11vw, 7rem)",
          textShadow: "4px 5px 0 var(--color-forest-dark)",
        }}
      >
        ASK ANYTHING
      </h1>
      <span
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-xl border-[3px] border-[var(--color-ink)] bg-[var(--color-pink)] px-3 py-1 font-mono text-[11px] font-bold tracking-[0.14em] text-white sm:px-4 sm:py-1.5 sm:text-sm"
        style={{ transform: "translate(-50%, -50%) rotate(-8deg)" }}
      >
        TASK 2
      </span>
    </div>
  );
}