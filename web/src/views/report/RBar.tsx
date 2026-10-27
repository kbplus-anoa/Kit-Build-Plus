/** 报告页顶栏：回主页、第几次提交、模式；目标图版本只在冻结后才有意义。 */
function BackIcon() {
  return (
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
      <path d="M14 6l-6 6 6 6" />
    </svg>
  );
}

export function RBar(props: {
  attempt: string;
  mode: "study" | "quiz";
  frozen: boolean;
  onHome: () => void;
}) {
  const mode = props.mode === "quiz" ? "测验模式" : "学习模式";
  const badge = props.frozen ? mode : mode + " · 未冻结";
  const live = props.frozen && props.mode === "quiz";
  return (
    <div className="rbar panel" style={{ ["--i" as string]: "0" }}>
      <button type="button" className="rbar__back" onClick={props.onHome}>
        <BackIcon />
        返回主页
      </button>
      <div className="rbar__context">
        <span className="rbar__sep" aria-hidden="true" hidden={!props.frozen}>·</span>
        <span id="report-attempt">{props.attempt || "本次提交"}</span>
        <span className="rbar__sep" aria-hidden="true">·</span>
        <span className={"rbar__badge" + (live ? " subbar__badge--live" : "")} id="mode-badge">
          {badge}
        </span>
      </div>
    </div>
  );
}
