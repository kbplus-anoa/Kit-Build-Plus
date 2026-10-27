/** 「继续」栏：后端存的草稿 + 未冻结的记录，都不混进历史报告。 */
import type { Attempt } from "../../data/attempt";
import type { DraftOut } from "../../types/api";
import { clockOf } from "./model";

function conceptCount(edges: Attempt["edges"]): number {
  const seen = new Set<string>();
  edges.forEach((edge) => {
    seen.add(edge.from);
    seen.add(edge.to);
  });
  return seen.size;
}

function modeName(mode: string): string {
  return mode === "test" ? "测验模式" : "学习模式";
}

function savedAt(iso: string): string {
  const at = Date.parse(iso);
  return Number.isNaN(at) ? "刚刚" : clockOf(at);
}

interface Props {
  records: Attempt[];
  drafts: DraftOut[];
  onOpen: (record: Attempt) => void;
  onRevise: (record: Attempt) => void;
  onResume: (draft: DraftOut) => void;
}

export function Holdings(props: Props) {
  const empty = props.drafts.length === 0 && props.records.length === 0;
  return (
    <section className="panel holdings" aria-labelledby="rb-holdings-title">
      <div className="holdings__head">
        <h2 className="holdings__title" id="rb-holdings-title">继续</h2>
        <p className="holdings__sub">学习模式可以继续修改，直到真正理解以至重建正确</p>
      </div>
      <div className="holdings__list">
        {empty ? (
          <p className="holdings__empty">还没有未冻结的重建。</p>
        ) : (
          <>
            {props.drafts.map((draft) => (
              <div className="holding" key={"draft-" + draft.material_id + "-" + draft.time_point}>
                <div className="holding__main">
                  <span className="holding__when">{savedAt(draft.saved_at)}</span>
                  <span className="holding__meta">
                    草稿 · {modeName(draft.mode)} · {draft.propositions.length} 条命题 ·{" "}
                    {conceptCount(
                      draft.propositions.map((prop) => ({
                        from: prop.head_id,
                        conn: prop.connection,
                        to: prop.tail_id,
                      })),
                    )}{" "}
                    个概念
                  </span>
                </div>
                <div className="holding__acts">
                  <button type="button" className="btn btn--ghost" onClick={() => props.onResume(draft)}>
                    继续
                  </button>
                </div>
              </div>
            ))}
            {props.records.map((record) => (
              <div className="holding" key={record.id}>
                <div className="holding__main">
                  <span className="holding__when">{record.when || "刚刚"}</span>
                  <span className="holding__meta">
                    学习模式 · {record.edges.length} 条命题 · {conceptCount(record.edges)} 个概念
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
            ))}
          </>
        )}
      </div>
    </section>
  );
}
