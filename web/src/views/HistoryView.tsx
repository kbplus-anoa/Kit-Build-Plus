/** 历史报告：只列已冻结的测验记录。 */
import { PageHead, SubBar } from "../../../ui-share/layout/SubBar";
import { scoreHeadline, tally, TARGET, type Attempt } from "../data/demo";
import type { Frame } from "../hooks/useRoute";
import { usePanelStagger } from "../hooks/usePanelStagger";
import { ReportShell } from "./ReportShell";

interface Props {
  frame: Frame;
  records: Attempt[];
  onHome: () => void;
  onOpen: (record: Attempt) => void;
}

function Score(props: { record: Attempt }) {
  return (
    <span className="rec__score">
      {tally(props.record.edges).correct} <small>/ {TARGET.length}</small>
    </span>
  );
}

export function HistoryView(props: Props) {
  const frozen = props.records.filter((record) => record.frozen);
  usePanelStagger("view-history", props.records);
  return (
    <ReportShell id="view-history" frame={props.frame}>
      <SubBar i={0} onHome={props.onHome} badge={frozen.length + " 份记录"} />
      <PageHead i={1} title="回顾先前的重建。" lede="学而时习之，不亦悦乎？" />
      <section className="panel">
        {frozen.length === 0 ? (
          <p className="history__empty">还没有冻结的记录。测验模式提交后会出现在这里。</p>
        ) : (
          <div className="history__list" id="history-list">
            {frozen.map((record, index) => (
              <button
                key={record.id}
                type="button"
                className={"rec" + (index === 0 ? " rec--current" : "")}
                style={{ ["--i" as string]: index }}
                onClick={() => props.onOpen(record)}
              >
                <span className="rec__main">
                  <span className="rec__head">
                    <span className="rec__when">{record.when}</span>
                    <span className="rec__mode">{record.mode === "quiz" ? "测验模式" : "学习模式"}</span>
                  </span>
                  <span className="rec__summary">{scoreHeadline(tally(record.edges), TARGET.length)}</span>
                </span>
                <Score record={record} />
              </button>
            ))}
          </div>
        )}
      </section>
      <div className="closing panel">
        <p className="closing__note">未冻结的学习记录，请回到「开始学习」页最下方查看。</p>
        <button type="button" className="btn btn--ghost" onClick={props.onHome}>
          返回主页
        </button>
      </div>
    </ReportShell>
  );
}