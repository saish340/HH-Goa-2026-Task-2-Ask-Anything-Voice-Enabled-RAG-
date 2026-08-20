import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { MicButton, type MicState } from "@/components/MicButton";
import { StatusLine, type Stage } from "@/components/StatusLine";
import { AnswerCard } from "@/components/AnswerCard";
import { StatsPanel } from "@/components/StatsPanel";
import { Wordmark } from "@/components/Wordmark";
import { SunsetBanner } from "@/components/SunsetBanner";
import { HangingCards } from "@/components/HangingCards";
import { ask, transcribe, type AskResponse } from "@/lib/api";

const TITLE = "Ask Anything — Voice RAG Demo · HH Goa 2026";
const DESC =
  "Speak a question and get a grounded, cited answer. Voice capture and transcription run as separate in-browser and network steps; hybrid retrieval + guarded generation answer in under 200ms (RAG-only latency, verified by benchmark).";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: TITLE },
      { name: "description", content: DESC },
      { property: "og:title", content: TITLE },
      { property: "og:description", content: DESC },
    ],
  }),
  component: Index,
});

const RECORD_MAX_MS = 8000;

type LangOption = { code: string; label: string; stt: string; ask: string | null };
const LANGUAGE_OPTIONS: LangOption[] = [
  { code: "auto", label: "Auto", stt: "en-IN", ask: null },
  { code: "en", label: "English", stt: "en-IN", ask: "en" },
  { code: "hi", label: "हिन्दी", stt: "hi-IN", ask: "hi" },
  { code: "mr", label: "मराठी", stt: "mr-IN", ask: "mr" },
  { code: "ur", label: "اردو", stt: "ur-IN", ask: "ur" },
];

function Index() {
  const [langCode, setLangCode] = useState<string>("auto");
  const [micState, setMicState] = useState<MicState>("idle");
  const [stage, setStage] = useState<Stage>("idle");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processingRef = useRef(false);
  const lang = LANGUAGE_OPTIONS.find((o) => o.code === langCode) ?? LANGUAGE_OPTIONS[0];
  const transcribeLabel = lang.code === "auto" ? "speech to text, auto-detected" : `speech to text, ${lang.stt}`;

  useEffect(() => {
    return () => {
      const recorder = recorderRef.current;
      if (recorder && recorder.state === "recording") recorder.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function startCapture() {
    setError(null);
    setTranscript(null);
    setResponse(null);

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      const reason =
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Microphone access was denied. Allow the microphone and try again."
          : err instanceof DOMException && err.name === "NotFoundError"
            ? "No microphone was found on this device."
            : "Could not start the microphone.";
      setError(reason);
      setMicState("idle");
      setStage("idle");
      return;
    }

    streamRef.current = stream;
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "";
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: BlobPart[] = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    recorder.onstop = () => {
      recorderRef.current = null;
      stream.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
      void finishCapture(blob);
    };

    recorder.start();
    recorderRef.current = recorder;
    setMicState("recording");
    setStage("listening...");

    window.setTimeout(() => {
      const r = recorderRef.current;
      if (r && r.state === "recording") r.stop();
    }, RECORD_MAX_MS);
  }

  async function finishCapture(blob: Blob) {
    if (processingRef.current) return;
    processingRef.current = true;
    setMicState("processing");
    setStage("transcribing...");
    try {
      const stt = await transcribe(blob, lang.stt);
      if (stt.error) throw new Error(stt.error);
      setTranscript(stt.transcript);

      setStage("retrieving...");
      const answer = await ask(stt.transcript, "fast", lang.ask);

      setStage("done");
      setMicState("done");
      setResponse(answer);
    } catch (err) {
      setMicState("idle");
      setStage("idle");
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      processingRef.current = false;
    }
  }

  async function run() {
    if (processingRef.current) return;
    const recorder = recorderRef.current;
    if (recorder && recorder.state === "recording") {
      recorder.stop();
      return;
    }
    await startCapture();
  }

  return (
    <main className="min-h-screen bg-[var(--color-forest)] font-mono">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-6">
        <span className="text-xs font-bold tracking-[0.2em] text-white uppercase">
          Ask Anything
        </span>
        <span className="text-[10px] tracking-[0.16em] text-[var(--color-cream)]/80 uppercase sm:text-xs">
          Goa, India · Task 2
        </span>
      </header>

      <div className="mx-auto max-w-3xl px-5">
        <section className="flex flex-col items-center text-center">
          <Wordmark />
          <h2
            className="font-display mt-8 font-bold text-white"
            style={{ fontSize: "clamp(1.8rem, 5vw, 3.2rem)", lineHeight: 1.08 }}
          >
            Speak a question, get a grounded answer.
          </h2>
          <p className="mt-5 max-w-xl text-[13px] leading-relaxed text-[var(--color-cream)]/85">
            Voice capture → transcription → hybrid retrieval → guarded generation. Every answer is
            cited, scored for confidence, and refused when the evidence doesn't hold up.
          </p>

          <label className="mt-7 inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-[var(--color-mustard)]">
            Language
            <select
              value={langCode}
              onChange={(e) => setLangCode(e.target.value)}
              className="cursor-pointer rounded-md border-2 border-[var(--color-mustard)] bg-[var(--color-forest-dark)] px-3 py-1.5 font-mono text-[12px] normal-case tracking-normal text-white outline-none hover:border-[var(--color-pink)] focus:border-[var(--color-pink)]"
            >
              {LANGUAGE_OPTIONS.map((o) => (
                <option key={o.code} value={o.code}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <div className="mt-14 mb-10">
            <MicButton state={micState} onClick={run} />
          </div>

          <StatusLine stage={stage} />

          {transcript && (
            <p className="animate-fade-slide-up mt-4 max-w-xl text-[13px] text-[var(--color-cream)] italic">
              “{transcript}”
            </p>
          )}

          {error && (
            <p
              role="alert"
              className="animate-fade-slide-up mt-4 max-w-xl rounded-lg border-2 border-[var(--color-pink)] bg-[var(--color-pink-soft)] px-4 py-3 text-[13px] leading-relaxed text-[var(--color-pink)]"
            >
              {error}
            </p>
          )}
        </section>
      </div>

      <div className="my-14 h-[180px] w-full overflow-hidden border-y-2 border-[var(--color-ink)] sm:h-[240px]">
        <SunsetBanner className="h-full w-full" />
      </div>

      <div className="mx-auto max-w-3xl px-5 pb-20">
        <HangingCards transcribeLabel={transcribeLabel} />

        {response && (
          <div className="mt-14">
            <AnswerCard response={response} />
          </div>
        )}

        <div className="mt-8">
          <StatsPanel />
        </div>

        <footer className="mt-14 flex flex-col items-center gap-3">
          <span className="rounded-full border-2 border-[var(--color-pink)] px-4 py-1.5 text-[11px] font-bold tracking-[0.14em] text-[var(--color-pink)]">
            #RAGInGoa
          </span>
          <p className="text-[11px] text-[var(--color-cream)]/70">
            Built for HH Goa 2026 · Task 2 — Ask Anything.
          </p>
        </footer>
      </div>
    </main>
  );
}
