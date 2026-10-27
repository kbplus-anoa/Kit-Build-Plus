/** 草稿只在这台设备上留一份，且只回到它被写下的那个模式里。 */
import type { Edge } from "../../data/demo";
import { DRAFT_KEY, MODE_KEY, sane, type At } from "./model";

export type Mode = "study" | "quiz";

export interface Draft {
  placed: Record<string, At>;
  mode: Mode | null;
  edges: Edge[];
  at: number;
}

export function readDraft(): Draft | null {
  try {
    const raw = window.localStorage.getItem(DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Draft>;
    if (!parsed || !Array.isArray(parsed.edges)) return null;
    return {
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
  try {
    window.localStorage.setItem(DRAFT_KEY, JSON.stringify({ placed, mode, edges, at }));
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
