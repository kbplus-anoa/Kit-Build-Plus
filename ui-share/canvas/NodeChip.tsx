/** 一个概念芯片：点一下是选中，拖是挪位置；刚放进画布的那一帧有一次入场。 */
import type { Box, KitConcept } from "./geometry";

interface Props {
  concept: KitConcept;
  box: Box;
  armed: boolean;
  used: boolean;
  entering: boolean;
  order: number;
  dragging: boolean;
  onPointerDown: (event: React.PointerEvent<SVGGElement>) => void;
  onEntered: () => void;
  onHover: (id: string | null) => void;
}

export function NodeChip(props: Props) {
  const { concept, box, armed, used, entering, order, dragging } = props;
  const cls =
    "rbn" +
    (armed ? " is-armed" : "") +
    (used ? " is-used" : "") +
    (entering ? " is-enter" : "") +
    (dragging ? " is-dragging" : "");
  return (
    <g
      className={cls}
      data-node={concept.id}
      style={entering ? ({ ["--i" as string]: order } as React.CSSProperties) : undefined}
      onPointerDown={props.onPointerDown}
      onPointerEnter={() => props.onHover(concept.id)}
      onPointerLeave={() => props.onHover(null)}
      onAnimationEnd={(event) => {
        if (event.animationName === "rb-node-in") props.onEntered();
      }}
    >
      <rect className="rbn__box" rx={8} x={box.x} y={box.y} width={box.w} height={box.h} />
      <text className="rbn__label" x={box.cx} y={box.cy + 4} textAnchor="middle">
        {concept.label}
      </text>
    </g>
  );
}
