const INK = "#14241B";
const CREAM = "#F7EFD9";
const MUSTARD = "#F5C518";
const FOREST = "#1B5E3A";
const FOREST_DARK = "#14492C";
const PINK = "#EC1E79";

function Palm({ x, flip = false }: { x: number; flip?: boolean }) {
  return (
    <g transform={`translate(${x} 0) ${flip ? "scale(-1,1)" : ""}`}>
      <path
        d="M0 200 C 6 150, 10 110, 4 62"
        stroke={INK}
        strokeWidth="9"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M0 200 C 6 150, 10 110, 4 62"
        stroke={CREAM}
        strokeWidth="5"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M0 200 C 6 150, 10 110, 4 62"
        stroke={MUSTARD}
        strokeWidth="1.4"
        fill="none"
      />
      {[
        "M4 62 C -22 42, -46 44, -58 58 C -40 50, -18 54, 4 62 Z",
        "M4 62 C 26 40, 52 42, 64 56 C 44 48, 22 52, 4 62 Z",
        "M4 62 C -12 34, -6 12, 10 4 C 6 24, 8 44, 4 62 Z",
        "M4 62 C 24 52, 44 62, 52 76 C 34 68, 18 66, 4 62 Z",
        "M4 62 C -18 54, -36 62, -44 76 C -26 68, -10 66, 4 62 Z",
      ].map((d, i) => (
        <path key={i} d={d} fill="#2C8A55" stroke={INK} strokeWidth="2.5" />
      ))}
    </g>
  );
}

export function SunsetBanner({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 800 200"
      preserveAspectRatio="xMidYMax slice"
      role="img"
      aria-label="Illustration of a sunset over a Goan beach"
      className={className}
    >
      <rect width="800" height="200" fill={FOREST} />
      {/* rays */}
      <g stroke={MUSTARD} strokeWidth="3" strokeLinecap="round">
        {[
          [400, 10, 400, 40],
          [340, 26, 352, 52],
          [460, 26, 448, 52],
          [292, 56, 312, 72],
          [508, 56, 488, 72],
          [262, 96, 288, 100],
          [538, 96, 512, 100],
          [370, 16, 378, 44],
        ].map(([x1, y1, x2, y2], i) => (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />
        ))}
      </g>
      {/* sun */}
      <path d="M340 120 A60 60 0 0 1 460 120 Z" fill={MUSTARD} />
      {/* horizon */}
      <line x1="0" y1="120" x2="800" y2="120" stroke={MUSTARD} strokeWidth="2.5" />
      {/* reflection */}
      <ellipse cx="400" cy="132" rx="46" ry="6" fill={MUSTARD} />
      <ellipse cx="400" cy="146" rx="30" ry="4.5" fill={MUSTARD} />
      {/* waves */}
      <g stroke={CREAM} strokeWidth="2.5" fill="none" strokeLinecap="round">
        <path d="M90 140 q 12 -6 24 0 t 24 0 t 24 0" />
        <path d="M600 150 q 12 -6 24 0 t 24 0 t 24 0" />
        <path d="M180 166 q 14 -6 28 0 t 28 0" />
      </g>
      {/* boat */}
      <g stroke={INK} strokeWidth="2.5" fill={CREAM}>
        <path d="M150 112 h44 l-8 10 h-30 z" />
        <rect x="164" y="102" width="14" height="10" />
      </g>
      {/* beach shack */}
      <g stroke={INK} strokeWidth="2.5">
        <rect x="630" y="150" width="110" height="46" fill={CREAM} />
        <rect x="622" y="138" width="126" height="14" fill={FOREST_DARK} />
        <rect x="650" y="160" width="70" height="16" fill={PINK} stroke={INK} />
      </g>
      <Palm x={60} />
      <Palm x={760} flip />
      <Palm x={250} />
    </svg>
  );
}