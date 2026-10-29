/** 未冻结的自检：目标图与分数都先不给。 */
export function HoldPanel(props: { hidden: boolean }) {
  return (
    <section className="panel hold" id="report-hold" hidden={props.hidden}>
      <p className="hold__tag mono">未冻结</p>
      <h2 className="hold__title">目标图先不显示。</h2>
      <p className="hold__body">
        目标图（差异图）会在冻结之后才出现。测验模式提交即冻结。
      </p>
    </section>
  );
}
