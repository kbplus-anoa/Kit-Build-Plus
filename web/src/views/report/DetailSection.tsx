/** 逐条明细：冻结后是目标图的判定，未冻结只看自己连上的命题。 */
import { DetailRows } from "./DetailRows";
import type { ReportState } from "./useReportView";

export function DetailSection(props: { state: ReportState; title: string }) {
  const { state } = props;
  const shown = state.filter === "all" ? "" : `，显示 ${state.shown} 条`;
  return (
    <section className="panel detail">
      <div className="detail__head">
        <h2 className="detail__title">{props.title}</h2>
        <p className="detail__count">
          共 {state.items.length} 条{shown}
        </p>
      </div>
      <DetailRows
        items={state.items}
        hidden={state.hidden}
        selected={state.selected}
        onSelect={state.setSelected}
      />
    </section>
  );
}
