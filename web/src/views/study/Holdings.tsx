/** 未冻结的记录留在这里，不混进历史报告。 */
import type { Attempt } from "../../data/attempt";

function conceptCount(record: Attempt): number {
  const seen = new Set<string>();
  record.edges.forEach((edge) => {
    seen.add(edge.from);
    seen.add(edge.to);
  });
  return seen.size;
}

interface Props {
  records: Attempt[];
  onOpen: (record: Attempt) => void;
  onRevise: (record: Attempt) => void;
}

export function Holdings(props: Props) {
  return (
    <section className="panel holdings" aria-labelledby="rb-holdings-title">
      <div className="holdings__head">
        <h2 className="holdings__title" id="rb-holdings-title">继续</h2>
        <p className="holdings__sub">学习模式可以继续修改，直到真正理解以至重建正确</p>
      </div>
      <div className="holdings__list">
        {props.records.length === 0 ? (
          <p className="holdings__empty">
            还没有未冻结的重建。
          </p>
        ) : (
          props.records.map((record) => (
            <div className="holding" key={record.id}>
              <div className="holding__main">
                <span className="holding__when">{record.when || "刚刚"}</span>
                <span className="holding__meta">
                  学习模式 · {record.edges.length} 条命题 · {conceptCount(record)} 个概念
                </span>
              </div>
              <div className="holding__acts">
                <button
                  type="button"
                  className="btn btn--ghost"
                  aria-label={
                    "查看 " + (record.when || "刚刚") + " 的自检：错误类型与你当前连上的命题，不含目标图"
                  }
                  onClick={() => props.onOpen(record)}
                >
                  查看报告
                </button>
                <button type="button" className="btn btn--ghost" onClick={() => props.onRevise(record)}>
                  继续修改
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
