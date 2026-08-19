# Goa Voice Q&A

What to build

A single-page web app called "Ask Anything" — a voice-enabled RAG (Retrieval- Augmented Generation) demo built for a hackathon (HH Goa 2026, Task #2). The user taps a mic button, speaks a question, and sees: a live transcript, a staged status indicator (listening → transcribing → retrieving → generating → done), then an answer card showing the generated answer, its source citations, a confidence score, and the response latency in milliseconds.

Status: implemented and wired to the real backend. The UI calls FastAPI through
`src/lib/api.ts` — voice is captured with the browser `MediaRecorder`, uploaded to
`POST /api/transcribe`, and the transcript is sent to `POST /api/ask`; the Stats
panel reads `GET /api/benchmarks`. Set `VITE_API_BASE` to the deployed backend
origin (defaults to `http://127.0.0.1:8001`). The real backend mounts everything
under `/api` (see `backend/app/main.py`). This doc below is the original Lovable
build spec, kept for reference.

Real API contract — this is the ACTUAL backend schema, not a guess

The backend is already built. Build the UI's TypeScript types and mock data to match this exactly, so swapping the mock for the real calls later is a drop-in replacement, not a reshape.

There are two real calls, because voice goes through a separate transcription step before the RAG call:

ts
// STEP 1 — POST /api/transcribe  (multipart/form-data: file=<audio blob>, language="en-IN" query param)
interface TranscribeResponse {
  transcript: string;
  confidence: number;   // 0–1
  language: string;
  duration_ms: number;
  error: string | null;
}

// STEP 2 — POST /ask  (JSON body)
interface AskRequest {
  query: string;              // the transcript from step 1
  language?: string | null;
  tier?: "fast" | "llm";      // default "fast" (extractive, low-latency tier)
}

interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  chunk_strategy: string;   // e.g. "sentence" | "semantic" | "sliding_window"
  position: number;
  token_count: number;
  language: string;
  text: string;
  score: number;
}

interface AskResponse {
  query: string;
  normalized_query: string;
  language: string;
  retrieved_chunks: RetrievedChunk[];
  scores: number[];
  answer: string;
  grounded: boolean;
  grounding_label: string;      // "SUPPORTED" | "UNSUPPORTED"
  grounding_score: number;
  confidence: number;           // 0–1
  latency_ms: number;
  per_stage_ms: Record<string, number>;
  strategy_used: string;
  generation_method: "extractive" | "llm";
  degraded: boolean;
  status: "ok" | "refused" | "error";
  error: string | null;
  sources: string[];            // flat array of source labels, e.g. ["Passage #18472", "Passage #72891"] — render each directly as a chip, don't expect an object shape
  version: string;
}

// GET /benchmarks — powers the Stats panel
interface BenchmarksResponse {
  available: boolean;
  p50?: number; p70?: number; p100?: number;
  stage_p50_ms?: Record<string, number>;
  recall_at_5?: number; recall_at_10?: number; mrr?: number;
  grounded_rate?: number; refusal_rate?: number; overall_accuracy?: number;
  per_category?: Record<string, unknown>;
}

// GET /stats — corpus/index info, optional secondary display
interface StatsResponse {
  corpus_passages: number;
  chunks: number;
  per_strategy: Record<string, number>;
  embedding_dim: number;
}

Refusal handling: there is no separate refusal_reason field. When the guardrail blocks an answer, status is "refused" and the human-readable refusal message is already in answer — so the refusal UI state should just check response.status === "refused" and render response.answer as the message, with sources/confidence omitted or hidden since they won't be meaningful in that case. Same pattern for status === "error" using response.error.

The real calls live in `src/lib/api.ts`: `transcribe(blob)` → `POST {API_BASE}/api/transcribe?language=…` (multipart `file`), `ask(query, tier)` → `POST {API_BASE}/api/ask` (JSON), plus `benchmarks()`/`stats()`. The `/api` prefix is required — the FastAPI app mounts its routes under `/api`, so do not call `/ask` or `/transcribe` bare.

Visual theme — retro tropical travel-poster (this is the REAL HH Goa brand, follow it exactly)

This is not a dark, minimal tech aesthetic. It's a bold, illustrated, high- saturation retro travel-poster look: deep forest green fields, mustard yellow and hot pink accents, cream cards, thick black illustration outlines, a display serif for headlines, and monospace for everything else (labels, body copy, data). Lean into it — playful and confident, not restrained.

Color tokens
css
--color-forest: #1B5E3A;        /* primary page background */
--color-forest-dark: #14492C;   /* depth/shadow variant */
--color-mustard: #F5C518;       /* accent yellow */
--color-mustard-soft: #FBE38A;  /* soft yellow, hover/fill */
--color-pink: #EC1E79;          /* primary accent, CTAs, labels */
--color-pink-soft: #F9C9DE;     /* soft pink, chip backgrounds */
--color-cream: #F7EFD9;         /* card background */
--color-cream-alt: #FBF6E8;     /* lighter card variant */
--color-ink: #14241B;           /* near-black text on cream, and outline color */
--color-white: #FFFFFF;

/* Status colors — must stay legible on cream cards, so keep them muted, not neon */
--status-good: #1B5E3A;
--status-warn: #C98A1B;
--status-bad: #C21E4A;

Page background is forest green everywhere — not just an accent strip. Cards sit on top of it in cream. Never use a dark navy/near-black background.

Typography
Display/headline font: Fraunces (Google Font) — bold weight, used for big headlines. Has an editorial, high-contrast, slightly vintage poster feel.
Everything else — body copy, labels, buttons, data, UI chrome: Space Mono (Google Font). The real brand keeps monospace even in paragraph- length text; don't substitute a humanist sans anywhere.
Load both via Google Fonts in the project setup.
Shape & style rules
Cards: cream background, 20px border-radius, generous padding (~32px), soft subtle drop shadow (not heavy/dark).
Buttons: fully pill-shaped (border-radius: 999px).
Primary CTA: solid hot pink fill, white bold text, no border.
Secondary: transparent/cream fill, pink outline, pink text.
Chips/badges (status pill, source chips, hashtag chip): pill-shaped, thin ink-colored or pink-colored border (2px), matching the hand-drawn outline character of the brand rather than a soft modern shadow style.
Use flat solid colors throughout — no gradients, no soft glows/blurs. The brand look comes from bold flat color blocks and thick outlines, not glass/ gradient effects.
The MicButton — build this exactly to spec (direct reference from HH Goa's own task icon)

This is the centerpiece of the hero. Build it precisely:

A solid dark forest-green circle, ~150px diameter, as the base.
Centered inside: a simple white line-drawn microphone icon (outlined SVG, medium stroke weight — not a filled glyph, not an icon-font character).
A dashed hot-pink circular ring, offset a few pixels outside the green circle's edge, drawn permanently (not just on hover/focus).
A small solid mustard-yellow circular badge (~28px) positioned at the top-right of the button, overlapping the dashed ring slightly, with a tiny dark-green icon inside it (e.g. a small settings/equalizer glyph).
A small white rounded tag/card positioned overlapping the bottom-left of the circle, containing: a tiny 3-4 bar waveform icon in forest green, and the text ASK ANYTHING in hot pink, bold, small-caps, Space Mono.
States
Idle: static, as described above.
Listening (mic active, before speech detected): the dashed pink ring rotates slowly and continuously (@keyframes rotate, ~10s linear infinite).
Recording (speech being captured): swap the static mic icon for a live waveform animation (thin vertical bars in a mix of pink/mustard/cream, animating height via CSS or randomized/audio-amplitude-driven values), ring keeps rotating.
Processing (after recording stops): ring keeps rotating, mic icon returns but at reduced opacity, paired with the StatusLine below stepping through stages.
Screens / layout
1. Header bar
Left: small wordmark ASK ANYTHING, Space Mono, uppercase, bold, white, small size, top-left corner.
Right: GOA, INDIA · TASK 2, Space Mono, small, cream/white, top-right.
2. Hero section
Centered layout on the forest-green background.
Headline in Fraunces, bold, large (clamp between ~2.5rem mobile and 4.5rem desktop), white text: "Speak a question, get a grounded answer."
Subtext below, Space Mono, smaller, light cream color, 1–2 lines describing the pipeline (voice → transcription → hybrid retrieval → guarded generation).
The MicButton, centered below the subtext, large and prominent.
Below the MicButton: a StatusLine — a pill-shaped chip (pink outline, soft pink fill --color-pink-soft, pink Space Mono text) that's empty/hidden at idle and shows the current stage once a query starts: listening... → transcribing... → retrieving... → generating... → done. Only one stage shown at a time, animate the text swap with a quick fade/slide.
Below that: a live transcript line — once STT "completes" (mocked), show the recognized text in a simple italic Space Mono line, quotation-marked.
3. Answer card (appears after the mocked pipeline completes)
Cream card (per card style above), appears with a gentle fade/slide-up entrance animation.
Small pink eyebrow label at the top, uppercase, bold, Space Mono, small size: ANSWER.
Answer text below in Space Mono, dark ink color (--color-ink), comfortable line-height (1.6+).
A row of source chips below the answer — one pill per string in the sources array (already formatted server-side, e.g. "Passage #18472" — just render each string directly, don't try to parse or restructure it), Space Mono, small, ink-colored border, cream/white fill; on hover, border becomes pink and the chip lifts slightly (translateY(-1px)).
A bottom strip inside the card (top border, small top padding) showing two data points in Space Mono, small size: Confidence: 94% and Latency: 143ms — color each value using the status tokens: green-ish if latency < 200ms and confidence high, amber if borderline, pink/red if latency exceeds budget or confidence is low. Base thresholds on the real measured fast-tier numbers (P50 ≈68ms, P100 ≈131ms, target <200ms): latency good <100ms, warn 100–200ms, bad >200ms; confidence good >80%, warn 50–80%, bad <50%. Define these as named constants at the top of the component file so they're easy to retune later against fresh benchmark output.
4. Refusal state (status === "refused")
Instead of the normal answer card, show a cream card with a pink-outlined (not solid) treatment, an ink-colored icon or small pink "!" badge, and the message from response.answer directly (mock a couple of realistic examples: "I couldn't find relevant information in the provided knowledge base." / "I couldn't verify that answer from the available sources.").
Still show latency_ms, but omit confidence/sources since nothing was retrieved or grounded in this case.
Handle status === "error" similarly, showing response.error instead.
5. Stats panel (small, optional secondary section below the main flow)
A cream card styled like the answer card, pink eyebrow label BENCHMARKS, simple two-column Space Mono key/value grid. This maps to the real GET /benchmarks response shape (p50, p70, p100, recall_at_5, recall_at_10, mrr, grounded_rate, refusal_rate, overall_accuracy) — mock data with that exact shape (including available: true) so wiring the real GET call later is a one-line swap. Handle available: false gracefully (e.g. "Not yet benchmarked").
6. Footer
Small pill chip: #RAGInGoa, pink outline, Space Mono, on the green background.
Line underneath, muted cream Space Mono text: Built for HH Goa 2026 · Task 2 — Ask Anything.
Interaction flow (real, in src/routes/index.tsx)
User clicks/taps the MicButton → `getUserMedia({ audio: true })` starts the mic; once permission is granted the button shows the "recording" waveform and StatusLine shows listening... (auto-stops at 8s, or tap again to stop early).
On stop the captured `webm` blob is sent to `transcribe()` → StatusLine steps transcribing... → retrieving... → generating... → done, revealing the transcript line.
`ask(transcript, "fast")` resolves to the real answer; branch on `status`:
"ok" → render the AnswerCard (answer + source chips + confidence + real latency_ms).
"refused"/"error" → render the refusal/error card (message from `answer`/`error`, latency only).
Permission denial or a failed /api call shows an inline error with the message — the page never silently stalls.

Use 3–4 different mock Q&A pairs (rotate between them) so repeated demo runs don't look identical — keep them generic/plausible RAG answers, not tied to real MSMARCO content since this is just UI mock data.

Technical requirements
React + TypeScript + Tailwind CSS (Lovable's default stack is fine).
Fully responsive: works cleanly at mobile (~390px) and desktop (~1440px) widths — the MicButton and answer card should scale/reflow sensibly, not just shrink text.
Respect prefers-reduced-motion: fall back to static (non-rotating, non-pulsing) states when set (already implemented in src/styles.css).
No gradients, no glassmorphism, no soft neon glows — flat color blocks, thick outlines where illustrative elements appear, pill shapes for buttons/chips, serif display + monospace body throughout.

Build it now.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/1c694c3a-5808-4e0e-9fe4-55b93c1f580f).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
