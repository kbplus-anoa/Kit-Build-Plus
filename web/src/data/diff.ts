/** 把学生图与目标图对齐，得出每一条命题的判定。判定只在报告页出现。 */
import { TARGET, type Edge } from "./demo";
import type { DiffItem } from "../../../ui-share/canvas/diffTypes";

function samePair(a: Edge, b: Edge): boolean {
  return (a.from === b.from && a.to === b.to) || (a.from === b.to && a.to === b.from);
}

export function buildItems(edges: Edge[]): DiffItem[] {
  const used = new Set<number>();
  const items: DiffItem[] = [];

  for (const target of TARGET) {
    const index = edges.findIndex((edge, i) => !used.has(i) && samePair(edge, target));
    if (index < 0) {
      items.push({ from: target.from, conn: target.conn, to: target.to, kind: "lacking" });
      continue;
    }
    used.add(index);
    const mine = edges[index];
    const sameWay = mine.from === target.from && mine.to === target.to;
    const kind = !sameWay ? "reversed" : mine.conn === target.conn ? "correct" : "leaving";
    items.push({ from: mine.from, conn: mine.conn, to: mine.to, kind });
  }

  edges.forEach((edge, index) => {
    if (used.has(index)) return;
    items.push({ from: edge.from, conn: edge.conn, to: edge.to, kind: "excessive" });
  });

  return items;
}
