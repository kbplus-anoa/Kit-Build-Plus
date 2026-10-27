/** 差异图的节点：只画被这一版判定用到的概念，可以像重建画布一样拖动。 */
import { boxOf, type KitConcept } from "./geometry";

interface Props {
  concepts: KitConcept[];
  needed: Set<string>;
  touched: Set<string>;
  dragging: string | null;
  onGrab: (event: React.PointerEvent<SVGGElement>, id: string) => void;
}

/** 被筛掉的节点留在场上淡出，不直接拆掉，否则线条消失时框会先没影。 */
export function DiffNodes(props: Props) {
  let order = 0;
  return (
    <g>
      {props.concepts
        .filter((concept) => props.needed.has(concept.label))
        .map((concept) => {
          const box = boxOf(concept, concept);
          const index = order;
          order += 1;
          const hidden = !props.touched.has(concept.label);
          return (
            <g
              key={concept.id}
              className={
                "dnode" + (hidden ? " is-hidden" : "") + (props.dragging === concept.id ? " is-dragging" : "")
              }
              style={{ ["--i" as string]: String(index) }}
              onPointerDown={(event) => props.onGrab(event, concept.id)}
            >
              <rect className="dnode__box" rx={8} x={box.x} y={box.y} width={box.w} height={box.h} />
              <text className="dnode__label" x={box.cx} y={box.cy + 5} textAnchor="middle">
                {concept.label}
              </text>
            </g>
          );
        })}
    </g>
  );
}
