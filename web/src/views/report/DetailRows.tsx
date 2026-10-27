/** 逐条明细：一条命题一行，点一行在图上聚焦它。 */
import { Mark } from "../../../../ui-share/atoms/Mark";
import type { DiffItem } from "../../../../ui-share/canvas/diffTypes";
import { LABEL, NOTE } from "../../data/reportText";

interface Props {
  items: DiffItem[];
  hidden: Set<number>;
  selected: number | null;
  onSelect: (index: number) => void;
}

function Empty() {
  return (
    <div className="empty" id="empty">
      <p className="empty__title">这个筛选下没有条目</p>
      <p className="empty__body">切回“全部”即可看到这张图的全部条目。</p>
    </div>
  );
}

export function DetailRows(props: Props) {
  if (props.items.length === 0 || props.items.length === props.hidden.size) return <Empty />;
  return (
    <div className="rows" id="rows">
      {props.items.map((item, index) =>
        props.hidden.has(index) ? null : (
          <button
            key={item.from + item.conn + item.to + index}
            type="button"
            className={"row" + (props.selected === index ? " is-focus" : "")}
            style={{ ["--i" as string]: String(index) }}
            onClick={() => props.onSelect(index)}
          >
            <span className={"row__mark row__mark--" + item.kind} aria-hidden="true">
              <Mark kind={item.kind} />
            </span>
            <span className="row__body">
              <span className="row__prop">
                <span className="ct">{item.from}</span> — {item.conn} → <span className="ct">{item.to}</span>
              </span>
              <span className="row__meta">{NOTE[item.kind]}</span>
            </span>
            <span className="row__tag">{LABEL[item.kind]}</span>
          </button>
        ),
      )}
    </div>
  );
}
