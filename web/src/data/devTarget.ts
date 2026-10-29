/** 开发者模式改目标图：加一条、删一条、把一条换成别的三段。 */
import type { Edge, Kit } from "./kit";

export function targetOf(kit: Kit): Edge[] {
  return kit.target ?? [];
}

/** 三段都必须是现成的零件，且不能自己连自己。 */
export function validEdge(ids: string[], words: string[], edge: Edge): boolean {
  if (!ids.includes(edge.from) || !ids.includes(edge.to)) return false;
  if (!words.includes(edge.conn)) return false;
  return edge.from !== edge.to;
}

function same(a: Edge, b: Edge): boolean {
  return a.from === b.from && a.conn === b.conn && a.to === b.to;
}

/** 加不进就返回 null：越界、自环、重复都不收。 */
export function addTargetEdge(
  edges: Edge[], ids: string[], words: string[], edge: Edge,
): Edge[] | null {
  if (!validEdge(ids, words, edge)) return null;
  if (edges.some((item) => same(item, edge))) return null;
  return [...edges, { from: edge.from, conn: edge.conn, to: edge.to }];
}

export function removeTargetEdge(edges: Edge[], edge: Edge): Edge[] {
  return edges.filter((item) => !same(item, edge));
}

/** 把 old 那一条换成 next；next 不成立或撞上别的命题就不收。 */
export function replaceTargetEdge(
  edges: Edge[], ids: string[], words: string[], old: Edge, next: Edge,
): Edge[] | null {
  if (!validEdge(ids, words, next)) return null;
  if (same(old, next)) return edges;
  if (edges.some((item) => same(item, next) && !same(item, old))) return null;
  return edges.map((item) => (same(item, old) ? { from: next.from, conn: next.conn, to: next.to } : item));
}

/** 概念或连接词没了，目标图里用到它的命题一并撤下。 */
export function pruneTarget(edges: Edge[], ids: string[], words: string[]): Edge[] {
  return edges.filter((edge) => validEdge(ids, words, edge));
}
