/** 差异图的手摆位置：按一次提交的快照分开存，换一份报告就换一套坐标。 */
export type Layout = Record<string, { x: number; y: number }>;

const KEY = "kbp-diff-layout:";

function sane(value: unknown): { x: number; y: number } | null {
  if (!value || typeof value !== "object") return null;
  const at = value as { x?: unknown; y?: unknown };
  if (typeof at.x !== "number" || typeof at.y !== "number") return null;
  if (!Number.isFinite(at.x) || !Number.isFinite(at.y)) return null;
  return { x: at.x, y: at.y };
}

export function readLayout(id: string): Layout {
  try {
    const raw = window.localStorage.getItem(KEY + id);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    const out: Layout = {};
    Object.entries(parsed as Record<string, unknown>).forEach(([concept, value]) => {
      const at = sane(value);
      if (at) out[concept] = at;
    });
    return out;
  } catch {
    return {};
  }
}

export function writeLayout(id: string, layout: Layout): void {
  try {
    window.localStorage.setItem(KEY + id, JSON.stringify(layout));
  } catch {
    /* 存不下就只留当前这一屏 */
  }
}
