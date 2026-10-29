/** 常驻提示条：错误用 alert 立刻念出来，其余用 status 轻声播报。
 *  样式类由调用方给（各页的边距与色彩略有差别），这里只负责角色与语义配对，
 *  免得每个页面各自手写 role，写漏一个屏幕阅读器就听不到错误。 */
import type { ReactNode } from "react";

export type NoticeTone = "error" | "done" | "note";

interface Props {
  tone: NoticeTone;
  className?: string;
  id?: string;
  hidden?: boolean;
  children: ReactNode;
}

export function Notice(props: Props) {
  return (
    <p
      className={props.className}
      id={props.id}
      hidden={props.hidden}
      role={props.tone === "error" ? "alert" : "status"}
    >
      {props.children}
    </p>
  );
}
