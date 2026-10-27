/**
 * 一次提交的本地快照：报告页与历史页只认这份，不再回头查后端。
 * 目标命题、错误链、标签与坐标都在提交那一刻冻结下来。
 */
import type { DiffItem } from "../../../ui-share/canvas/diffTypes";
import type { KitConcept } from "../../../ui-share/canvas/geometry";
import type { ErrorChain } from "../types/api";
import type { Edge } from "./kit";
import type { Kind } from "./reportText";

export interface Attempt {
  id: string;
  materialId: number;
  material: string;
  mapVersion: string;
  mode: "study" | "quiz";
  attempt: string;
  when: string;
  frozen: boolean;
  edges: Edge[];
  target: Edge[];
  errors: ErrorChain[];
  labels: Record<string, string>;
  layout: Record<string, { x: number; y: number }>;
  total: number;
  correct: number;
  fms: number;
}

const ERROR_KIND: Record<string, Kind> = {
  lacking: "lacking",
  excessive: "excessive",
  leaving: "leaving",
  reversed: "reversed",
};

function keyOf(from: string, conn: string, to: string): string {
  return from + "\u0000" + conn + "\u0000" + to;
}

export function countsOf(record: Attempt): Record<Kind, number> {
  const counts: Record<Kind, number> = {
    correct: record.correct,
    lacking: 0,
    excessive: 0,
    leaving: 0,
    reversed: 0,
  };
  record.errors.forEach((error) => {
    const kind = ERROR_KIND[error.kind];
    if (kind) counts[kind] += 1;
  });
  return counts;
}

/** 冻结报告：目标图里的每条都在，没连上的补成缺失；学生多出来的接在后面。 */
export function itemsOf(record: Attempt): DiffItem[] {
  const nameOf = (id: string) => record.labels[id] ?? id;
  const drawn = new Set(record.edges.map((edge) => keyOf(edge.from, edge.conn, edge.to)));
  const shown = new Map<string, Kind>();
  record.errors.forEach((error) => {
    const kind = ERROR_KIND[error.kind];
    if (kind) shown.set(keyOf(error.head_id, error.connection, error.tail_id), kind);
  });
  const items: DiffItem[] = [];
  record.target.forEach((goal) => {
    const key = keyOf(goal.from, goal.conn, goal.to);
    const kind: Kind | undefined = drawn.has(key) ? "correct" : shown.get(key);
    if (kind === "correct" || kind === "lacking") {
      items.push({ from: nameOf(goal.from), to: nameOf(goal.to), conn: goal.conn, kind });
    }
  });
  record.edges.forEach((edge) => {
    const kind = shown.get(keyOf(edge.from, edge.conn, edge.to));
    if (kind && kind !== "lacking") {
      items.push({ from: nameOf(edge.from), to: nameOf(edge.to), conn: edge.conn, kind });
    }
  });
  return items;
}

export function conceptsOf(record: Attempt): KitConcept[] {
  return Object.entries(record.labels).map(([id, label]) => {
    const at = record.layout[id] ?? { x: 0, y: 0 };
    return { id, label, x: at.x, y: at.y };
  });
}
