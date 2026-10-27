/**
 * 重建画布：固定 960×540 的 SVG 场。
 * 只报告点了谁、拖到哪、选中哪条，不对错与否做判断。
 */

import { useCallback, useState } from "react";

import { EdgeLine } from "./EdgeLine";
import { boxOf, edgeGeometry, type CanvasEdge, type KitConcept } from "./geometry";
import { MarkerDefs } from "./MarkerDefs";
import { NodeChip } from "./NodeChip";
import { toCanvas, useNodeDrag, VIEW_H, VIEW_W } from "./useNodeDrag";

export interface RebuildCanvasProps {
  concepts: KitConcept[];
  placed: Record<string, { x: number; y: number }>;
  edges: CanvasEdge[];
  armedId?: string | null;
  entering: string[];
  locked?: boolean;
  selected: number | null;
  drawAt: number | null;
  onConcept: (id: string) => void;
  onEntered: (id: string) => void;
  onPlaced: (id: string, x: number, y: number) => void;
  onEdge: (index: number) => void;
  onMove: (id: string, x: number, y: number) => void;
  onBlank: () => void;
  onDrawn: () => void;
}

export function RebuildCanvas(props: RebuildCanvasProps) {
  const { concepts, placed, edges, armedId = null, entering, locked = false, selected, drawAt } = props;
  const { onConcept, onEdge, onMove, onEntered, onPlaced, onBlank, onDrawn } = props;
  const [hovered, setHovered] = useState<string | null>(null);

  const placedAt = useCallback(
    (concept: KitConcept) => placed[concept.id] ?? { x: concept.x, y: concept.y },
    [placed],
  );
  const drag = useNodeDrag({ concepts, placedAt, locked, onMove, onPick: onConcept });
  const shown = concepts.filter((concept) => placed[concept.id]);
  const neighbours = edges.map((edge) => [edge.from, edge.to]).flat();

  const draft = (() => {
    if (!armedId || !hovered || hovered === armedId) return null;
    const from = shown.find((concept) => concept.id === armedId);
    const to = shown.find((concept) => concept.id === hovered);
    if (!from || !to) return null;
    return { a: placedAt(from), b: placedAt(to) };
  })();

  return (
    <svg
      className="rb-svg"
      id="rb-canvas"
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      role="application"
      aria-disabled={locked ? "true" : undefined}
      aria-label="重建画布：把左侧的概念放进画布，点两个概念，再选中间的连接词，就完成一条命题。"
      onPointerDown={(event) => {
        if (event.target !== event.currentTarget) return;
        onBlank();
      }}
      onDragOver={(event) => {
        if (locked) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
      }}
      onDrop={(event) => {
        event.preventDefault();
        if (locked) return;
        const id = event.dataTransfer.getData("text/plain");
        if (!id) return;
        const at = toCanvas(event.currentTarget, event.clientX, event.clientY);
        onPlaced(id, at.x, at.y);
      }}
    >
      <MarkerDefs />
      {draft ? (
        <line className="rbe rbe--draft" x1={draft.a.x} y1={draft.a.y} x2={draft.b.x} y2={draft.b.y} />
      ) : null}
      <g>
        {edges.map((edge, index) => {
          const from = concepts.find((concept) => concept.id === edge.from);
          const to = concepts.find((concept) => concept.id === edge.to);
          if (!from || !to || !placed[from.id] || !placed[to.id]) return null;
          return (
            <EdgeLine
              key={`${edge.from}-${edge.conn}-${edge.to}-${index}`}
              head={from.label}
              conn={edge.conn}
              tail={to.label}
              geo={edgeGeometry(edge, index, edges, boxOf(from, placedAt(from)), boxOf(to, placedAt(to)))}
              selected={selected === index}
              drawing={drawAt === index}
              locked={locked}
              onPick={() => onEdge(index)}
              onKey={() => onEdge(index)}
              onDrawn={onDrawn}
            />
          );
        })}
      </g>
      <g>
        {shown.map((concept) => (
          <NodeChip
            key={concept.id}
            concept={concept}
            box={boxOf(concept, placedAt(concept))}
            armed={armedId === concept.id}
            used={neighbours.includes(concept.id)}
            entering={entering.includes(concept.id)}
            order={Math.max(0, entering.indexOf(concept.id))}
            dragging={drag.dragging === concept.id}
            onPointerDown={(event) => drag.start(event, concept.id)}
            onEntered={() => onEntered(concept.id)}
            onHover={setHovered}
          />
        ))}
      </g>
    </svg>
  );
}
