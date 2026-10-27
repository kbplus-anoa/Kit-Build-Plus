/**
 * 点选与拖动共用一个指针手势：位移小于阈值算点击，否则算拖动。
 * 坐标一律经 SVG 的 CTM 反变换；按容器宽度比例换算，遇上黑边 y 会偏。
 */

import { useEffect, useRef, useState } from "react";

import { CHIP_H, chipWidth, type KitConcept } from "./geometry";

export const VIEW_W = 960;
export const VIEW_H = 540;
const DRAG_THRESHOLD = 5;

export function toCanvas(svg: SVGSVGElement, clientX: number, clientY: number) {
  const ctm = svg.getScreenCTM();
  if (!ctm) {
    const rect = svg.getBoundingClientRect();
    return {
      x: ((clientX - rect.left) / rect.width) * VIEW_W,
      y: ((clientY - rect.top) / rect.height) * VIEW_H,
    };
  }
  const point = new DOMPoint(clientX, clientY).matrixTransform(ctm.inverse());
  return { x: point.x, y: point.y };
}

interface DragState {
  id: string;
  from: { x: number; y: number };
  origin: { x: number; y: number };
  moved: boolean;
}

interface Options {
  concepts: KitConcept[];
  placedAt: (concept: KitConcept) => { x: number; y: number };
  locked: boolean;
  onMove: (id: string, x: number, y: number) => void;
  onPick: (id: string) => void;
}

export function useNodeDrag(options: Options) {
  const { concepts, placedAt, locked, onMove, onPick } = options;
  const drag = useRef<DragState | null>(null);
  const detach = useRef<(() => void) | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);

  useEffect(() => () => detach.current?.(), []);

  function stop() {
    detach.current?.();
    detach.current = null;
    drag.current = null;
    setDragging(null);
  }

  function start(event: React.PointerEvent<SVGGElement>, id: string) {
    if (locked) return;
    const svg = event.currentTarget.ownerSVGElement;
    const concept = concepts.find((item) => item.id === id);
    if (!svg || !concept) return;
    event.preventDefault();
    const from = toCanvas(svg, event.clientX, event.clientY);
    drag.current = { id, from, origin: placedAt(concept), moved: false };

    const onPointerMove = (moveEvent: PointerEvent) => {
      const state = drag.current;
      if (!state) return;
      const at = toCanvas(svg, moveEvent.clientX, moveEvent.clientY);
      const dx = at.x - state.from.x;
      const dy = at.y - state.from.y;
      if (!state.moved) {
        if (Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
        state.moved = true;
        setDragging(state.id);
      }
      const half = chipWidth(concept.label) / 2;
      const x = Math.min(VIEW_W - half - 4, Math.max(half + 4, state.origin.x + dx));
      const y = Math.min(VIEW_H - CHIP_H / 2 - 4, Math.max(CHIP_H / 2 + 4, state.origin.y + dy));
      onMove(state.id, x, y);
    };

    const onPointerUp = () => {
      const state = drag.current;
      stop();
      if (state && !state.moved) onPick(state.id);
    };

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
    window.addEventListener("blur", onPointerUp);
    detach.current = () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);
      window.removeEventListener("blur", onPointerUp);
    };
  }

  return { start, dragging };
}
