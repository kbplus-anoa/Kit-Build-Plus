/** 画布底栏：模式与状态在左，动作在右。状态只说事实，不给操作提示。 */
import type { Edge } from "../../data/demo";
import { clockOf, usedConceptCount } from "./model";

interface Props {
  mode: "study" | "quiz";
  locked: boolean;
  edges: Edge[];
  savedAt: number | null;
  dirty: boolean;
  onUndo: () => void;
  onClear: () => void;
  onSave: () => void;
  onSubmit: () => void;
}

export function RebuildBar(props: Props) {
  const modeCls = "rb__mode " + (props.locked ? "rb__mode--locked" : "rb__mode--open");
  const modeText =
    props.mode === "study" ? "学习模式 · 提交后可返回修改" : "测验模式 · 提交后不可修改";
  return (
    <div className="rb__bar">
      <span className={modeCls}>{modeText}</span>
      <p className="rb__status">
        <b>{props.edges.length}</b> 条命题 · <b>{usedConceptCount(props.edges)}</b> 个概念 ·{" "}
        {props.savedAt ? (
          <>
            已保存 <b>{clockOf(props.savedAt)}</b>
          </>
        ) : props.dirty ? (
          "有未保存的改动"
        ) : (
          "还没有保存过"
        )}
      </p>
      <div className="rb__grow" />
      <button type="button" className="btn btn--ghost" onClick={props.onUndo} disabled={props.locked}>
        撤销
      </button>
      <button type="button" className="btn btn--ghost" onClick={props.onClear} disabled={props.locked}>
        清空
      </button>
      <button type="button" className="btn btn--ghost" onClick={props.onSave} disabled={props.locked}>
        存草稿
      </button>
      <button type="button" className="btn btn--primary" onClick={props.onSubmit} disabled={props.locked}>
        提交
      </button>
    </div>
  );
}
