/** 与后端通信的唯一出口：路径、错误解析、请求形状都收在这里。 */
import type {
  ConfigIn,
  ConfigOut,
  HealthOut,
  KitAutoIn,
  KitAutoOut,
  MaterialsOut,
  MaterialTextOut,
  SubmitIn,
  SubmitOut,
  UploadOut,
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

function postJson<T>(path: string, body: unknown): Promise<T> {
  return send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
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

  submit: (body: SubmitIn): Promise<SubmitOut> => postJson<SubmitOut>("/api/submit", body),

  config: (): Promise<ConfigOut> => send<ConfigOut>("/api/config", { method: "GET" }),

  saveConfig: (body: ConfigIn): Promise<ConfigOut> =>
    send<ConfigOut>("/api/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
