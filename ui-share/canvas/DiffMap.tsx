/** 差异图：同一张概念图，连对走主色，四类差异只改形状。 */
import { useEffect, useState } from "react";

import { DiffEdgeLayer } from "./DiffEdge";
import { DiffMarkerDefs } from "./DiffMarkerDefs";
import { DiffNodes } from "./DiffNodes";
import type { DiffFilter, DiffItem } from "./diffTypes";
import type { KitConcept } from "./geometry";

export type { DiffFilter, DiffItem } from "./diffTypes";

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
}

export function DiffMap(props: Props) {
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
  const draw = useDrawIn(props.items.length, props.stamp);
  return (
    <svg
      id="diffmap"
      viewBox="0 0 960 540"
      role="img"
      aria-label="概念图差异示意图。"
      data-drawing={draw.drawing.size > 0 ? "true" : undefined}
    >
      <DiffMarkerDefs />
      <DiffEdgeLayer
        items={props.items}
        concepts={props.concepts}
        shown={shown}
        selected={props.selected}
        drawing={draw.drawing}
        onDrawn={draw.done}
        onSelect={props.onSelect}
      />
      <DiffNodes concepts={props.concepts} needed={needed} touched={touched} />
    </svg>
  );
}
