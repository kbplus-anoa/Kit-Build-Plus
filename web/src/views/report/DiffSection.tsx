/** 差异图与筛选：条件切换只改可见性，不改判定。 */
import { DiffMap } from "../../../../ui-share/canvas/DiffMap";
import { CONCEPTS } from "../../data/demo";
import { Legend } from "./Legend";
import type { ReportState } from "./useReportView";

export function DiffSection(props: { state: ReportState; stamp: string }) {
  const { items, filters, filter, setFilter, selected, setSelected } = props.state;
  return (
    <section className="panel diff">
      <div className="diff__head">
        <h2 className="diff__title">差异图</h2>
        <div className="diff__filters">
          {filters.map((option) => (
            <button
              key={option.id}
              type="button"
              className={"chip" + (filter === option.id ? " chip--active" : "")}
              data-filter={option.id}
              aria-pressed={filter === option.id}
              onClick={() => setFilter(option.id)}
            >
              {option.label}
              <span className="mono">{option.count}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="diff__canvas-wrap">
        <DiffMap
          concepts={CONCEPTS}
          items={items}
          filter={filter}
          selected={selected}
          onSelect={setSelected}
          stamp={props.stamp}
        />
      </div>
      <Legend filter={filter} />
    </section>
  );
}
