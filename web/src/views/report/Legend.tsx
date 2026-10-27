/** 图例：五种笔迹各代表什么，跟着当前筛选一起收窄。 */
import { Mark } from "../../../../ui-share/atoms/Mark";
import type { DiffFilter } from "../../../../ui-share/canvas/diffTypes";
import { LABEL, LEGEND_DESC, type Kind } from "../../data/reportText";

const KINDS: Kind[] = ["correct", "lacking", "excessive", "leaving", "reversed"];

function shows(kind: Kind, filter: DiffFilter): boolean {
  if (filter === "correct") return kind === "correct";
  if (filter === "error") return kind !== "correct";
  return true;
}

export function Legend(props: { filter: DiffFilter }) {
  return (
    <div className="legend" id="legend">
      {KINDS.filter((kind) => shows(kind, props.filter)).map((kind) => (
        <span key={kind} className={"legend__item legend__item--" + kind}>
          <Mark kind={kind} size={16} />
          <span>{LABEL[kind]}</span>
          <span className="mono legend__desc">{LEGEND_DESC[kind]}</span>
        </span>
      ))}
    </div>
  );
}
