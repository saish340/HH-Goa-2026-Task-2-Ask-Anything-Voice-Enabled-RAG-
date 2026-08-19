/**
 * Real backend client. The FastAPI app mounts everything under /api (see
 * backend/app/main.py), so the deployed VITE_API_BASE points at the backend
 * origin and we append the /api prefix here.
 *
 *   transcribe -> POST /api/transcribe (multipart/form-data: file, language=?query)
 *   ask        -> POST /api/ask        (JSON body)
 *   benchmarks -> GET  /api/benchmarks
 *   stats      -> GET  /api/stats
 */

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://127.0.0.1:8001";

export interface TranscribeResponse {
  transcript: string;
  confidence: number;
  language: string;
  duration_ms: number;
  error: string | null;
}

export interface AskRequest {
  query: string;
  language?: string | null;
  tier?: "fast" | "llm";
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  chunk_strategy: string;
  position: number;
  token_count: number;
  language: string;
  text: string;
  score: number;
}

export interface AskResponse {
  query: string;
  normalized_query: string;
  language: string;
  retrieved_chunks: RetrievedChunk[];
  scores: number[];
  answer: string;
  grounded: boolean;
  grounding_label: string;
  grounding_score: number;
  confidence: number;
  latency_ms: number;
  per_stage_ms: Record<string, number>;
  strategy_used: string;
  generation_method: "extractive" | "llm";
  degraded: boolean;
  status: "ok" | "refused" | "error";
  error: string | null;
  sources: string[];
  version: string;
}

export interface BenchmarksResponse {
  available: boolean;
  p50?: number;
  p70?: number;
  p100?: number;
  stage_p50_ms?: Record<string, number>;
  recall_at_5?: number;
  recall_at_10?: number;
  mrr?: number;
  grounded_rate?: number;
  refusal_rate?: number;
  overall_accuracy?: number;
  per_category?: Record<string, unknown>;
}

export interface StatsResponse {
  corpus_passages: number;
  chunks: number;
  per_strategy: Record<string, number>;
  embedding_dim: number;
}

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Backend error (${res.status}): ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function transcribe(blob: Blob, language = "en-IN"): Promise<TranscribeResponse> {
  const form = new FormData();
  form.append("file", blob, "recording.webm");
  const res = await fetch(`${API_BASE}/api/transcribe?language=${encodeURIComponent(language)}`, {
    method: "POST",
    body: form,
  });
  return jsonOrThrow<TranscribeResponse>(res);
}

export async function ask(
  query: string,
  tier: "fast" | "llm" = "fast",
  language: string | null = null,
): Promise<AskResponse> {
  const body: AskRequest = { query, tier };
  if (language) body.language = language;
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return jsonOrThrow<AskResponse>(res);
}

export async function benchmarks(): Promise<BenchmarksResponse> {
  return jsonOrThrow<BenchmarksResponse>(await fetch(`${API_BASE}/api/benchmarks`));
}

export async function stats(): Promise<StatsResponse> {
  return jsonOrThrow<StatsResponse>(await fetch(`${API_BASE}/api/stats`));
}
