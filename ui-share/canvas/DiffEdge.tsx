/** 差异图的一条边：形状、连接词与命中区。 */
import { useLayoutEffect, useRef } from "react";

import { boxOf, edgeGeometry, type CanvasEdge, type EdgeGeometry, type KitConcept } from "./geometry";
import type { DiffItem } from "./diffTypes";

interface EdgeProps {
  item: DiffItem;
  geo: EdgeGeometry;
  index: number;
  hidden: boolean;
  focused: boolean;
  dim: boolean;
  drawing: boolean;
  onDrawn: () => void;
  onSelect: () => void;
}

/** 一份判定在图上留下的那条线，以及它自己的描边入场。 */
function DiffEdge(props: EdgeProps) {
  const { item, geo, index, hidden, focused, dim, drawing } = props;
  const pathRef = useRef<SVGPathElement>(null);

  // 长度只能从画出来的路径量：画笔描边不需要在 JS 里再猜一遍几何。
  useLayoutEffect(() => {
    const path = pathRef.current;
    if (!path || !drawing) return;
    let len = 0;
    try {
      len = path.getTotalLength();
    } catch {
      len = 0;
    }
    if (len > 1) path.style.setProperty("--draw-len", len.toFixed(2));
    path.style.setProperty("--i", String(index));
  }, [drawing, index, geo.d]);

  const cls =
    `edge edge--${item.kind}` +
    (hidden ? " is-hidden" : "") +
    (focused ? " is-focus" : dim ? " is-dim" : "") +
    (drawing ? " is-drawing" : "");
  const labelCls = "edge-label" + (hidden ? " is-hidden" : "") + (focused ? " is-focus" : dim ? " is-dim" : "");
  const reverse = item.kind === "reversed";

  return (
    <g>
      <path
        ref={pathRef}
        className={cls}
        d={geo.d}
        fill="none"
        markerEnd={`url(#diff-arrow-${item.kind})`}
        markerStart={reverse ? `url(#diff-arrow-${item.kind})` : undefined}
        onAnimationEnd={props.onDrawn}
      />
      <text className={labelCls} x={geo.lx} y={geo.ly - 6} textAnchor="middle">
        {item.conn}
      </text>
      <path
        className="rbe-hit"
        d={geo.d}
        role="button"
        tabIndex={0}
        aria-label={`${item.from} ${item.conn} ${item.to}`}
        onClick={props.onSelect}
        onKeyDown={(event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          props.onSelect();
        }}
      />
    </g>
  );
}

interface LayerProps {
  items: DiffItem[];
  concepts: KitConcept[];
  shown: boolean[];
  selected: number | null;
  drawing: Set<number>;
  onDrawn: (index: number) => void;
  onSelect: (index: number) => void;
}

/** 判定按判定顺序入场，先连对的先画出来。 */
export function DiffEdgeLayer(props: LayerProps) {
  const edges: CanvasEdge[] = props.items.map((item) => ({ from: item.from, conn: item.conn, to: item.to }));
  const at = (label: string) => props.concepts.find((c) => c.label === label);
  return (
    <g>
      {props.items.map((item, index) => {
        const a = at(item.from);
        const b = at(item.to);
        if (!a || !b) return null;
        const geo = edgeGeometry(edges[index], index, edges, boxOf(a, a), boxOf(b, b));
        return (
          <DiffEdge
            key={`${item.from}-${item.conn}-${item.to}-${index}`}
            item={item}
            geo={geo}
            index={index}
            hidden={!props.shown[index]}
            focused={props.selected === index}
            dim={props.selected !== null && props.selected !== index}
            drawing={props.drawing.has(index)}
            onDrawn={() => props.onDrawn(index)}
            onSelect={() => props.onSelect(index)}
          />
        );
      })}
    </g>
  );
}
