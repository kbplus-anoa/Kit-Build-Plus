/** 零件栏的一组：可折叠，标题右侧带已用计数。 */
import type { ReactNode } from "react";

interface Props {
  title: string;
  count: number;
  total: number;
  children: ReactNode;
}

export function RailGroup(props: Props) {
  return (
    <details className="rail__group" open>
      <summary className="rail__summary">
        {props.title}
        <span className="mono" style={{ marginLeft: "auto" }}>
          {props.count} / {props.total}
        </span>
      </summary>
      <div className="rail__parts">{props.children}</div>
    </details>
  );
}
