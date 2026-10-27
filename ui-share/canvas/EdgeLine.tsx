/** 一条命题：连线、18px 命中带、连接词底板。刚连上的那条自己画出来。 */
import type { EdgeGeometry } from "./geometry";

interface Props {
  head: string;
  conn: string;
  tail: string;
  geo: EdgeGeometry;
  selected: boolean;
  drawing: boolean;
  locked: boolean;
  onPick: () => void;
  onKey: () => void;
  onDrawn: () => void;
}

export function EdgeLine(props: Props) {
  const { head, conn, tail, geo, selected, locked } = props;
  return (
    <g>
      <path
        className={"rbe" + (selected ? " is-selected" : "") + (props.drawing ? " is-draw" : "")}
        d={geo.d}
        pathLength={1}
        markerEnd={props.drawing ? undefined : "url(#rb-arrow)"}
        onAnimationEnd={(event) => {
          if (event.animationName === "rb-edge-in") props.onDrawn();
        }}
      />
      <path
        className="rbe-hit"
        d={geo.d}
        role="button"
        tabIndex={locked ? -1 : 0}
        aria-pressed={selected}
        aria-label={`${head} ${conn} ${tail}：按回车选中，选中后可以删除。`}
        onClick={props.onPick}
        onKeyDown={(event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          props.onKey();
        }}
      />
      <rect
        className="rbe__plate"
        rx={4}
        x={geo.lx - geo.plateW / 2}
        y={geo.ly - 9}
        width={geo.plateW}
        height={18}
      />
      <text className="rbe__label" x={geo.lx} y={geo.ly + 4} textAnchor="middle">
        {conn}
      </text>
    </g>
  );
}
