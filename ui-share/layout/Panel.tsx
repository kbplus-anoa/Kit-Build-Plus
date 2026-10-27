/** 报告页与子页的玻璃面板，i 决定入场错峰。 */
import type { CSSProperties, ReactNode } from "react";

export function Panel(props: {
  i: number;
  className?: string;
  id?: string;
  label?: string;
  children: ReactNode;
}) {
  const style = { "--i": String(props.i) } as CSSProperties;
  const cls = "panel" + (props.className ? " " + props.className : "");
  return (
    <section className={cls} style={style} id={props.id} aria-labelledby={props.label}>
      {props.children}
    </section>
  );
}
