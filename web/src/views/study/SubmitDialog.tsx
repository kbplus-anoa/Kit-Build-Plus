/** 提交前确认一次：命题数、概念数、评分口径与冻结规则。 */
import { useEffect, useRef } from "react";

import type { Edge } from "../../data/kit";
import type { StudyFlow } from "./useStudyFlow";

function conceptCount(edges: Edge[]): number {
  const seen = new Set<string>();
  edges.forEach((edge) => {
    seen.add(edge.from);
    seen.add(edge.to);
  });
  return seen.size;
}

export function SubmitDialog(props: { flow: StudyFlow; total: number }) {
  const { flow } = props;
  const dialog = useRef<HTMLDialogElement | null>(null);

  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (flow.confirming && !node.open) node.showModal();
    if (!flow.confirming && node.open) node.close();
  }, [flow.confirming]);

  return (
    <dialog className="confirm" ref={dialog} aria-labelledby="rb-confirm-title">
      <h2 className="confirm__title" id="rb-confirm-title">提交这一次的图？</h2>
      <p className="confirm__body">
        你连了 <b>{flow.api.edges.length}</b> 条命题，用了 <b>{conceptCount(flow.api.edges)}</b> 个概念。
        <br />
        提交后进入评分，分数 = 连对的命题数 / {props.total}，不给部分分。
      </p>
      <p className="confirm__warn">
        {flow.mode === "quiz"
          ? "测验模式：提交即冻结，这份图连同目标图一起进入历史报告，之后不可修改。"
          : "学习模式：提交后仍可修改，会留在「未冻结的重建」里，目标图此时不显示。"}
      </p>
      <div className="confirm__acts">
        <button type="button" className="btn btn--ghost" onClick={() => flow.setConfirming(false)}>
          再看看
        </button>
        <button type="button" className="btn btn--primary" onClick={flow.submit}>
          提交
        </button>
      </div>
    </dialog>
  );
}
