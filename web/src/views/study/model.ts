/** 画布的几何与词表小工具：放哪、怎么念、用了几件。 */
import { CHIP_H, chipWidth } from "../../../../ui-share/canvas/geometry";
import { concepts, known as inKit, labelOf as catalogLabel, type Edge } from "../../data/kit";

export const VIEW_W = 960;
export const VIEW_H = 540;
export const DRAFT_KEY = "kbp-draft";
export const MODE_KEY = "kbp-mode";

export interface At {
  x: number;
  y: number;
}

export function labelOf(id: string): string {
  return catalogLabel(id);
}

export function kitCount(): number {
  return concepts().length;
}

export function clampAt(id: string, x: number, y: number): At {
  const half = chipWidth(labelOf(id)) / 2;
  return {
    x: Math.min(VIEW_W - half - 4, Math.max(half + 4, x)),
    y: Math.min(VIEW_H - CHIP_H / 2 - 4, Math.max(CHIP_H / 2 + 4, y)),
  };
}

export function findSlot(placed: Record<string, At>, id: string): At {
  const cols = 4;
  const rows = 3;
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const x = 140 + col * ((VIEW_W - 280) / (cols - 1));
      const y = 120 + row * ((VIEW_H - 240) / (rows - 1));
      const taken = Object.values(placed).some(
        (at) => Math.abs(at.x - x) < 90 && Math.abs(at.y - y) < 60,
      );
      if (!taken) return clampAt(id, x, y);
    }
  }
  return clampAt(id, VIEW_W / 2, VIEW_H / 2);
}

export function seedPlacements(edges: Edge[]): Record<string, At> {
  const out: Record<string, At> = {};
  edges.forEach((edge) => {
    [edge.from, edge.to].forEach((id) => {
      if (out[id] || !inKit(id)) return;
      out[id] = findSlot(out, id);
    });
  });
  return out;
}

export function tripleOf(edge: Edge): string {
  return labelOf(edge.from) + " " + edge.conn + " " + labelOf(edge.to);
}

export function usedConceptCount(edges: Edge[]): number {
  const seen = new Set<string>();
  edges.forEach((edge) => {
    seen.add(edge.from);
    seen.add(edge.to);
  });
  return seen.size;
}

export function clockOf(at: number): string {
  const date = new Date(at);
  return (
    String(date.getHours()).padStart(2, "0") + ":" + String(date.getMinutes()).padStart(2, "0")
  );
}

export function sane(edge: Edge): boolean {
  return inKit(edge.from) && inKit(edge.to) && typeof edge.conn === "string";
}
