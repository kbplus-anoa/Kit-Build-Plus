/** 草稿只在这台设备上留一份，且只回到它被写下的那份 kit 与模式里。 */
import type { Edge } from "../../data/kit";
import { getKit } from "../../data/kit";
import { DRAFT_KEY, MODE_KEY, sane, type At } from "./model";

export type Mode = "study" | "quiz";

export interface Draft {
  materialId: number;
  mapVersion: string;
  placed: Record<string, At>;
  mode: Mode | null;
  edges: Edge[];
  at: number;
}

/** 只认同一份教材、同一个目标图版本的草稿，换教材后旧草稿直接作废。 */
export function readDraft(materialId: number, mapVersion: string): Draft | null {
  try {
    const raw = window.localStorage.getItem(DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Draft>;
    if (!parsed || !Array.isArray(parsed.edges)) return null;
    if (parsed.materialId !== materialId || parsed.mapVersion !== mapVersion) return null;
    return {
      materialId,
      mapVersion,
      placed: parsed.placed ?? {},
      mode: parsed.mode ?? null,
      edges: parsed.edges.filter(sane),
      at: typeof parsed.at === "number" ? parsed.at : Date.now(),
    };
  } catch {
    return null;
  }
}

export function writeDraft(mode: Mode, placed: Record<string, At>, edges: Edge[]): number | null {
  const at = Date.now();
  const kit = getKit();
  try {
    window.localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        materialId: kit?.materialId ?? 0,
        mapVersion: kit?.mapVersion ?? "",
        placed,
        mode,
        edges,
        at,
      }),
    );
  } catch {
    return null;
  }
  return at;
}

export function clearDraft(): void {
  try {
    window.localStorage.removeItem(DRAFT_KEY);
  } catch {
    /* a blocked store has nothing to clear */
  }
}

export function rememberMode(mode: Mode): void {
  try {
    window.localStorage.setItem(MODE_KEY, mode);
  } catch {
    /* the mode also lives in memory */
  }
}
