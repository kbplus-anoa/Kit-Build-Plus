/** 把开发者改动写进库：给叠层就整份覆盖，给 null 就撤销回冻结图。 */
import { api, ApiError } from "../../api/client";
import type { Overlay } from "../../data/devKit";
import { localStore, passOf } from "../../data/devLock";
import { getKit, type Edge } from "../../data/kit";
import type { DevKitIn, DevKitOut, PropositionIn } from "../../types/api";

interface Hooks {
  setBusy: (busy: boolean) => void;
  onDone: (body: DevKitOut) => void;
  onFail: (why: string) => void;
}

function propsOf(edges: Edge[]): PropositionIn[] {
  return edges.map((edge) => ({
    head_id: edge.from, connection: edge.conn, tail_id: edge.to,
  }));
}

function bodyOf(overlay: Overlay | null): DevKitIn | null {
  const kit = getKit();
  if (!kit) return null;
  const parts = overlay ?? { concepts: [], connections: [], target: [] };
  return {
    material_id: kit.materialId,
    map_version: kit.mapVersion,
    password: passOf(localStore()),
    concepts: parts.concepts.map((item) => ({ concept_id: item.id, label: item.label })),
    connections: parts.connections,
    propositions: propsOf(parts.target),
  };
}

function why(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return "开发者密码不对，关掉开关再打开一次。";
  }
  return error instanceof Error ? error.message : "改不动，稍后再试。";
}

export async function commitOverlay(overlay: Overlay | null, hooks: Hooks): Promise<void> {
  const body = bodyOf(overlay);
  if (!body) return;
  hooks.setBusy(true);
  try {
    const out = overlay ? await api.devSave(body) : await api.devReset(body);
    hooks.onDone(out);
  } catch (error) {
    hooks.onFail(why(error));
  } finally {
    hooks.setBusy(false);
  }
}
