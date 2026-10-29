/** 把概念从零件栏搬到画布的两个判断：够不够格算搬运，落点在不在画布上。 */
export interface Pt {
  x: number;
  y: number;
}

export interface Box {
  left: number;
  top: number;
  width: number;
  height: number;
}

export const CARRY_SLOP = 6;

export function carried(origin: Pt, now: Pt, slop: number = CARRY_SLOP): boolean {
  const dx = now.x - origin.x;
  const dy = now.y - origin.y;
  return Math.sqrt(dx * dx + dy * dy) >= slop;
}

export function onCanvas(box: Box, at: Pt): boolean {
  if (box.width <= 0 || box.height <= 0) return false;
  if (at.x < box.left || at.x > box.left + box.width) return false;
  if (at.y < box.top || at.y > box.top + box.height) return false;
  return true;
}
