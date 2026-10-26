/** 与后端通信的唯一出口。页面不直接 fetch，一律经此层。 */

import type {
  BatchIn,
  BatchOut,
  BuildKitIn,
  ExtractIn,
  ExtractOut,
  HealthOut,
  IngestIn,
  IngestOut,
  KitOut,
  QuestionRowIn,
  QuizIn,
  QuizOut,
  ReadyOut,
  ScoreOut,
  SubjectRowIn,
  SubmitIn,
} from "../types/api";

const BASE = "";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseError(resp: Response): Promise<string> {
  try {
    const body = await resp.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg ?? "").join("；");
    }
  } catch {
    /* 响应体不是 JSON，落到统一文案 */
  }
  return `请求失败（HTTP ${resp.status}）`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
  return (await resp.json()) as T;
}

async function requestBlob(path: string, body: unknown): Promise<Blob> {
  const resp = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
  return await resp.blob();
}

export const api = {
  health: () => request<HealthOut>("/api/health"),

  ingest: (body: IngestIn) =>
    request<IngestOut>("/api/ingest", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  extract: (body: ExtractIn) =>
    request<ExtractOut>("/api/extract", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  adjudicate: (body: BatchIn) =>
    request<BatchOut>("/api/adjudicate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  buildKit: (body: BuildKitIn) =>
    request<KitOut>("/api/kit", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  lockState: (mapVersion: string) =>
    request<ReadyOut>(
      `/api/lock?map_version=${encodeURIComponent(mapVersion)}`,
    ),

  submit: (body: SubmitIn) =>
    request<ScoreOut>("/api/submit", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  saveQuiz: (body: QuizIn) =>
    request<QuizOut>("/api/quiz", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  exportSubject: (rows: SubjectRowIn[]) =>
    requestBlob("/api/export/subject", { rows }),

  exportQuestion: (rows: QuestionRowIn[]) =>
    requestBlob("/api/export/question", { rows }),
};

/** 触发浏览器下载；BOM 由后端加，此处不碰字节。 */
export function downloadBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
}
