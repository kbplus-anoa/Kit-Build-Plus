/**
 * 画布几何：节点盒、连线出入点、同对多线的弯开量。
 * 只做坐标换算，不知道对错，也不读数据源。
 */

export const CHIP_H = 38;

export interface KitConcept {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface CanvasEdge {
  from: string;
  conn: string;
  to: string;
}

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
  cx: number;
  cy: number;
}

export function chipWidth(label: string): number {
  const n = String(label ?? "").length;
  return Math.max(84, Math.min(150, 26 + n * 15));
}

export function boxOf(concept: KitConcept, at: { x: number; y: number }): Box {
  const w = chipWidth(concept.label);
  return {
    x: at.x - w / 2,
    y: at.y - CHIP_H / 2,
    w,
    h: CHIP_H,
    cx: at.x,
    cy: at.y,
  };
}

export function exit(box: Box, tx: number, ty: number): { x: number; y: number } {
  const dx = tx - box.cx;
  const dy = ty - box.cy;
  if (!dx && !dy) return { x: box.cx, y: box.cy };
  const hw = box.w / 2 + 4;
  const hh = box.h / 2 + 4;
  const sx = dx === 0 ? Infinity : hw / Math.abs(dx);
  const sy = dy === 0 ? Infinity : hh / Math.abs(dy);
  const t = Math.min(sx, sy);
  return { x: box.cx + dx * t, y: box.cy + dy * t };
}

export function bowOf(index: number): number {
  if (!index) return 0;
  const flip = index % 2 === 1 ? 1 : -1;
  return flip * (34 + Math.floor((index - 1) / 2) * 26);
}

export function routeKey(edge: CanvasEdge): string {
  return [edge.from, edge.to].sort().join("\u0000");
}

export function bowIndex(edges: CanvasEdge[], index: number): number {
  const key = routeKey(edges[index]);
  let same = 0;
  for (let k = 0; k < index; k += 1) {
    if (routeKey(edges[k]) === key) same += 1;
  }
  return same;
}

export interface EdgeGeometry {
  d: string;
  lx: number;
  ly: number;
  plateW: number;
}

export function edgeGeometry(
  edge: CanvasEdge,
  index: number,
  edges: CanvasEdge[],
  a: Box,
  b: Box,
): EdgeGeometry {
  const p1 = exit(a, b.cx, b.cy);
  const p2 = exit(b, a.cx, a.cy);
  const bow = bowOf(bowIndex(edges, index));
  const mx = (p1.x + p2.x) / 2;
  const my = (p1.y + p2.y) / 2;

  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;

  const cxp = mx + nx * bow * 2;
  const cyp = my + ny * bow * 2;
  const d = bow
    ? `M${p1.x} ${p1.y} Q${cxp} ${cyp} ${p2.x} ${p2.y}`
    : `M${p1.x} ${p1.y} L${p2.x} ${p2.y}`;

  const lx = bow ? mx + nx * bow * 1.1 : mx;
  const ly = bow ? my + ny * bow * 1.1 : my;
  const label = String(edge.conn ?? "");
  const plateW = Math.max(28, [...label].length * 13 + 12);
  return { d, lx, ly, plateW };
}
