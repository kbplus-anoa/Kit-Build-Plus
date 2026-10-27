/** 子页顶栏：一个回主页的出口 + 右侧上下文。 */
import type { ReactNode } from "react";

const CHEVRON = (
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

export function SubBar(props: {
  i: number;
  onHome: () => void;
  badge: string;
  extra?: ReactNode;
  live?: boolean;
}) {
  return (
    <div className="subbar panel" style={{ ["--i" as string]: String(props.i) }}>
      <button type="button" className="subbar__back" onClick={props.onHome}>
        {CHEVRON}
        返回主页
      </button>
      <div className="subbar__context">
        {props.extra}
        {props.extra ? <span className="subbar__sep" aria-hidden="true">·</span> : null}
        <span className={"subbar__badge" + (props.live ? " subbar__badge--live" : "")}>
          {props.badge}
        </span>
      </div>
    </div>
  );
}

export function PageHead(props: { i: number; title: string; lede?: string }) {
  return (
    <div className="pagehead panel" style={{ ["--i" as string]: String(props.i) }}>
      <h1 className="pagehead__title">{props.title}</h1>
      {props.lede ? <p className="pagehead__lede">{props.lede}</p> : null}
    </div>
  );
}
