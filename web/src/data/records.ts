/** 提交快照只留在这台设备上：刷新之后，未冻结的重建与历史报告都还在。 */
import type { Attempt } from "./attempt";

const KEY = "kbp-records:v1";
const LIMIT = 50;

function isAt(value: unknown): boolean {
  if (!value || typeof value !== "object") return false;
  const at = value as { x?: unknown; y?: unknown };
  return typeof at.x === "number" && typeof at.y === "number";
}

function sane(value: unknown): Attempt | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Partial<Attempt>;
  if (typeof row.id !== "string" || !row.id) return null;
  if (typeof row.materialId !== "number" || typeof row.mapVersion !== "string") return null;
  if (!Array.isArray(row.edges) || !Array.isArray(row.target) || !Array.isArray(row.errors)) return null;
  if (!row.labels || typeof row.labels !== "object" || !row.layout || typeof row.layout !== "object") return null;
  if (typeof row.total !== "number" || typeof row.correct !== "number") return null;
  const layout: Attempt["layout"] = {};
  Object.entries(row.layout).forEach(([id, at]) => {
    if (isAt(at)) layout[id] = { x: (at as { x: number }).x, y: (at as { y: number }).y };
  });
  return {
    id: row.id,
    materialId: row.materialId,
    material: String(row.material ?? ""),
    mapVersion: row.mapVersion,
    mode: row.mode === "quiz" ? "quiz" : "study",
    attempt: String(row.attempt ?? "本次提交"),
    when: String(row.when ?? "刚刚"),
    frozen: Boolean(row.frozen),
    edges: row.edges,
    target: row.target,
    errors: row.errors,
    labels: row.labels as Record<string, string>,
    layout,
    total: row.total,
    correct: row.correct,
    fms: Number(row.fms ?? 0),
  };
}

export function readRecords(): Attempt[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.map(sane).filter((row): row is Attempt => row !== null).slice(0, LIMIT);
  } catch {
    return [];
  }
}

export function writeRecords(records: Attempt[]): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(records.slice(0, LIMIT)));
  } catch {
    /* 存不下就只留当前这一轮 */
  }
}
