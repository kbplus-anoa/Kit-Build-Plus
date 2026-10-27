/** 报告页收尾：未冻结时回画布继续改，冻结后只留一句说明。 */
export function Closing(props: { frozen: boolean; onRevise: () => void }) {
  return (
    <div className="closing panel">
      <button
        type="button"
        className="btn btn--primary"
        id="revise"
        hidden={props.frozen}
        onClick={props.onRevise}
      >
        继续修改这张图
        <svg
          className="od-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M6 12h12M14 7l5 5-5 5" />
        </svg>
      </button>
      <p className="closing__note" id="closing-note">
        {props.frozen
          ? "这次提交的成绩已记录。测验模式提交后不可修改，这份报告就是那一次的快照。"
          : "学习模式可以反复回到画布继续改；冻结之后（测验模式提交）才会评分，并显示目标图。"}
      </p>
    </div>
  );
}
