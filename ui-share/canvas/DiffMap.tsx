/** 差异图：同一张概念图，连对走主色，四类差异只改形状；概念可以拖动。 */
import { useEffect, useRef, useState } from "react";

import { DiffEdgeLayer } from "./DiffEdge";
import { DiffMarkerDefs } from "./DiffMarkerDefs";
import { DiffNodes } from "./DiffNodes";
import type { DiffFilter, DiffItem } from "./diffTypes";
import type { KitConcept } from "./geometry";
import { useNodeDrag } from "./useNodeDrag";

export type { DiffFilter, DiffItem } from "./diffTypes";

export type DiffLayout = Record<string, { x: number; y: number }>;

function visible(item: DiffItem, filter: DiffFilter): boolean {
  if (filter === "error") return item.kind !== "correct";
  if (filter === "correct") return item.kind === "correct";
  return true;
}

/** 两帧之后再开画：路由在同一帧里翻 report-open，入场不该和整张图抢那一帧。 */
function useDrawIn(count: number, key: string) {
  const [drawing, setDrawing] = useState<Set<number>>(new Set());
  const [drawn, setDrawn] = useState<Set<number>>(new Set());

  useEffect(() => {
    setDrawing(new Set());
    setDrawn(new Set());
    let second = 0;
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(() => {
        const next = new Set<number>();
        for (let index = 0; index < count; index += 1) next.add(index);
        setDrawing(next);
      });
    });
    return () => {
      cancelAnimationFrame(first);
      cancelAnimationFrame(second);
    };
  }, [count, key]);

  const done = (index: number) => {
    setDrawn((prev) => (prev.has(index) ? prev : new Set(prev).add(index)));
  };

  const active = new Set<number>();
  drawing.forEach((index) => {
    if (!drawn.has(index)) active.add(index);
  });
  return { drawing: active, done };
}

interface Props {
  concepts: KitConcept[];
  items: DiffItem[];
  filter: DiffFilter;
  selected: number | null;
  onSelect: (index: number) => void;
  stamp: string;
  layoutKey: string;
  layout: DiffLayout;
  onLayout: (next: DiffLayout) => void;
}

export function DiffMap(props: Props) {
  const [at, setAt] = useState<DiffLayout>(props.layout);
  const atRef = useRef(at);
  atRef.current = at;

  // 换一份报告就换一套坐标，同一份报告里拖动不会被重置。
  useEffect(() => {
    setAt(props.layout);
    atRef.current = props.layout;
  }, [props.layoutKey]);

  const shown = props.items.map((item) => visible(item, props.filter));
  const needed = new Set<string>();
  const touched = new Set<string>();
  props.items.forEach((item, index) => {
    needed.add(item.from);
    needed.add(item.to);
    if (!shown[index]) return;
    touched.add(item.from);
    touched.add(item.to);
  });

  const nodes = props.concepts.map((concept) => {
    const place = at[concept.id];
    return place ? { ...concept, x: place.x, y: place.y } : concept;
  });

  const drag = useNodeDrag({
    concepts: nodes,
    placedAt: (concept) => ({ x: concept.x, y: concept.y }),
    locked: false,
    onMove: (id, x, y) => {
      const next = { ...atRef.current, [id]: { x, y } };
      atRef.current = next;
      setAt(next);
    },
    onPick: () => undefined,
    onDrop: () => props.onLayout(atRef.current),
  });

  const draw = useDrawIn(props.items.length, props.stamp);
  return (
    <svg
      id="diffmap"
      viewBox="0 0 960 540"
      role="img"
      aria-label="概念图差异示意图，概念可以拖动调整位置。"
      data-drawing={draw.drawing.size > 0 ? "true" : undefined}
    >
      <DiffMarkerDefs />
      <DiffEdgeLayer
        items={props.items}
        concepts={nodes}
        shown={shown}
        selected={props.selected}
        drawing={draw.drawing}
        onDrawn={draw.done}
        onSelect={props.onSelect}
      />
      <DiffNodes
        concepts={nodes}
        needed={needed}
        touched={touched}
        dragging={drag.dragging}
        onGrab={(event, id) => drag.start(event, id)}
      />
    </svg>
  );
}
