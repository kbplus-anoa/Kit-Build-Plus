/** 与后端通信的唯一出口：路径、错误解析、请求形状都收在这里。 */
import type {
  ConfigIn,
  ConfigOut,
  CurrentDraftIn,
  DevKitIn,
  DevKitOut,
  DraftOut,
  DraftsOut,
  HealthOut,
  KitAutoIn,
  KitAutoOut,
  KitOut,
  KitUseOut,
  KitVersionsOut,
  MaterialsOut,
  MaterialTextOut,
  RecordsOut,
  SubmitIn,
  SubmitOut,
  UploadOut,
} from "../types/api";
import type { ExportPreviewOut } from "../types/export";

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
    const data = (await resp.json()) as { detail?: unknown };
    if (typeof data.detail === "string") return data.detail;
    if (data.detail) return JSON.stringify(data.detail);
  } catch {
    // 非 JSON 响应就退回状态码
  }
  return `请求失败（${resp.status}）`;
}

async function send<T>(path: string, init: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(BASE + path, init);
  } catch {
    throw new ApiError(0, "连不上后端服务，请确认它已经在运行。");
  }
  if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
  return (await resp.json()) as T;
}

function json(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return send<T>(path, json("POST", body));
}

function query(params: Record<string, string | number | undefined>): string {
  const parts = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== "")
    .map(([key, value]) => key + "=" + encodeURIComponent(String(value)));
  return parts.length ? "?" + parts.join("&") : "";
}

/** 同名参数要重复给（被试/教材/时点都可多选），上面的 query 只认单值。 */
function repeated(key: string, values: Array<string | number> | undefined): string[] {
  if (!values || values.length === 0) return [];
  return values.map((value) => key + "=" + encodeURIComponent(String(value)));
}

function fileNameOf(resp: Response, fallback: string): string {
  const raw = resp.headers.get("Content-Disposition") ?? "";
  const hit = /filename="?([^";]+)"?/.exec(raw);
  return hit ? hit[1] : fallback;
}

/** 二进制响应走不了 send()：它假定 JSON，这里原样收 blob 并带回文件名。 */
async function download(path: string, fallback: string): Promise<{ blob: Blob; name: string }> {
  let resp: Response;
  try {
    resp = await fetch(BASE + path);
  } catch {
    throw new ApiError(0, "连不上后端服务，请确认它已经在运行。");
  }
  if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
  return { blob: await resp.blob(), name: fileNameOf(resp, fallback) };
}

export interface ExportFilter {
  participantIds?: number[];
  materialIds?: number[];
  timePoints?: string[];
}

export const api = {
  health: (): Promise<HealthOut> => send<HealthOut>("/api/health", { method: "GET" }),

  upload: (file: File): Promise<UploadOut> => {
    const form = new FormData();
    form.append("file", file);
    return send<UploadOut>("/api/upload", { method: "POST", body: form });
  },

  materials: (): Promise<MaterialsOut> => send<MaterialsOut>("/api/materials", { method: "GET" }),

  materialText: (materialId: number): Promise<MaterialTextOut> =>
    send<MaterialTextOut>(`/api/materials/${materialId}/text`, { method: "GET" }),

  removeMaterial: (materialId: number): Promise<{ ok: boolean }> =>
    send<{ ok: boolean }>(`/api/materials/${materialId}`, { method: "DELETE" }),

  kitAuto: (body: KitAutoIn): Promise<KitAutoOut> => postJson<KitAutoOut>("/api/kit/auto", body),

  kitVersions: (materialId: number): Promise<KitVersionsOut> =>
    send<KitVersionsOut>("/api/kit/versions" + query({ material_id: materialId }), {
      method: "GET",
    }),

  kitVersion: (materialId: number, mapVersion: string): Promise<KitOut> =>
    send<KitOut>(
      "/api/kit/entry" + query({ material_id: materialId, map_version: mapVersion }),
      { method: "GET" },
    ),

  kitUse: (materialId: number, mapVersion: string): Promise<KitUseOut> =>
    postJson<KitUseOut>("/api/kit/use", { material_id: materialId, map_version: mapVersion }),

  devKit: (materialId: number, mapVersion: string): Promise<DevKitOut> =>
    send<DevKitOut>(
      "/api/dev/kit" + query({ material_id: materialId, map_version: mapVersion }),
      { method: "GET" },
    ),

  devSave: (body: DevKitIn): Promise<DevKitOut> =>
    send<DevKitOut>("/api/dev/kit", json("PUT", body)),

  devReset: (body: DevKitIn): Promise<DevKitOut> =>
    send<DevKitOut>("/api/dev/kit", json("DELETE", body)),

  submit: (body: SubmitIn): Promise<SubmitOut> => postJson<SubmitOut>("/api/submit", body),

  records: (participantId: number, materialId?: number): Promise<RecordsOut> =>
    send<RecordsOut>("/api/records" + query({ participant_id: participantId, material_id: materialId }), {
      method: "GET",
    }),

  drafts: (participantId: number): Promise<DraftsOut> =>
    send<DraftsOut>("/api/drafts" + query({ participant_id: participantId }), { method: "GET" }),

  currentDraft: (participantId: number, materialId: number, timePoint: string): Promise<DraftOut> =>
    send<DraftOut>(
      "/api/draft/current" + query({ participant_id: participantId, material_id: materialId, time_point: timePoint }),
      { method: "GET" },
    ),

  saveCurrent: (body: CurrentDraftIn): Promise<DraftOut> =>
    postJson<DraftOut>("/api/draft/current", body),

  exportSubject: (filter: ExportFilter): Promise<{ blob: Blob; name: string }> => {
    const parts = [
      ...repeated("participant_id", filter.participantIds),
      ...repeated("material_id", filter.materialIds),
      ...repeated("time_point", filter.timePoints),
    ];
    const path = "/api/export/subject" + (parts.length ? "?" + parts.join("&") : "");
    return download(path, "subject.csv");
  },

  exportPreview: (filter: ExportFilter, limit = 8): Promise<ExportPreviewOut> => {
    const parts = [
      ...repeated("participant_id", filter.participantIds),
      ...repeated("material_id", filter.materialIds),
      ...repeated("time_point", filter.timePoints),
      "limit=" + limit,
    ];
    return send<ExportPreviewOut>("/api/export/preview?" + parts.join("&"), {
      method: "GET",
    });
  },

  config: (): Promise<ConfigOut> => send<ConfigOut>("/api/config", { method: "GET" }),

  saveConfig: (body: ConfigIn): Promise<ConfigOut> =>
    send<ConfigOut>("/api/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
