/** 子页面版式：玻璃底 + 面板入场。入场由路由加 report-open，离场由路由挂 is-leaving。 */
import { type ReactNode } from "react";

import type { Frame } from "../hooks/useRoute";

export function ReportShell(props: {
  id: string;
  frame: Frame;
  extra?: string;
  children: ReactNode;
}) {
  const { frame, extra } = props;
  const style = frame.leaving ? { top: frame.leavingTop } : undefined;
  return (
    <div
      className={"report" + (extra ? " " + extra : "") + (frame.leaving ? " is-leaving" : "")}
      id={props.id}
      hidden={frame.hidden}
      style={style}
    >
      <div className="report__veil" aria-hidden="true" />
      <div className="report__inner">{props.children}</div>
    </div>
  );
}
