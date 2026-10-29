/** 手指把零件从栏里拎到画布：跟手影、够格才算搬运、落点在画布上才按落点放。 */
import { useEffect, useRef, useState } from "react";

import { toCanvas } from "../../../../ui-share/canvas/useNodeDrag";
import { carried, onCanvas, type Pt } from "./carry";

export interface Ghost extends Pt {
  label: string;
}

interface Args {
  locked: boolean;
  onDrop: (id: string, at: Pt | null) => void;
}

function dropTarget(at: Pt): Pt | null {
  const svg = document.getElementById("rb-canvas");
  if (!(svg instanceof SVGSVGElement)) return null;
  if (!onCanvas(svg.getBoundingClientRect(), at)) return null;
  return toCanvas(svg, at.x, at.y);
}

export function useCarry(args: Args) {
  const [ghost, setGhost] = useState<Ghost | null>(null);
  const detach = useRef<(() => void) | null>(null);
  const swallowed = useRef(false);

  useEffect(() => () => detach.current?.(), []);

  function start(event: React.PointerEvent<HTMLElement>, id: string, label: string) {
    if (args.locked || event.pointerType === "mouse") return;
    /* 上一次搬运可能根本没补出 click；新的手势先把旧账清掉 */
    swallowed.current = false;
    const pointerId = event.pointerId;
    const origin = { x: event.clientX, y: event.clientY };
    let moved = false;

    function stop() {
      detach.current?.();
      detach.current = null;
      setGhost(null);
    }

    function onMove(move: PointerEvent) {
      if (move.pointerId !== pointerId) return;
      const now = { x: move.clientX, y: move.clientY };
      if (!moved && !carried(origin, now)) return;
      moved = true;
      setGhost({ label, x: now.x, y: now.y });
    }

    function onUp(up: PointerEvent) {
      if (up.pointerId !== pointerId) return;
      const carriedOut = moved;
      stop();
      if (!carriedOut) return;
      swallowed.current = true;
      args.onDrop(id, dropTarget({ x: up.clientX, y: up.clientY }));
    }

    function onCancel(cancel: PointerEvent) {
      if (cancel.pointerId !== pointerId) return;
      stop();
    }

    detach.current?.();
    detach.current = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onCancel);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onCancel);
  }

  /** 搬完那一下浏览器还会补一个 click，不收下就会再放一次。 */
  function tookClick(): boolean {
    if (!swallowed.current) return false;
    swallowed.current = false;
    return true;
  }

  return { ghost, start, tookClick };
}
