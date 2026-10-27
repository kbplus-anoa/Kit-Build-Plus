/** 分数只报一个数：目标命题里连对了几条。 */
import type { ReactNode } from "react";

import { scoreHeadline, type Kind } from "../../data/reportText";

function part(count: number, label: string): ReactNode {
  return (
    <span key={label}>
      {count} 条<strong>{label}</strong>
    </span>
  );
}

function joined(nodes: ReactNode[]): ReactNode[] {
  return nodes.flatMap((node, index) => (index === 0 ? [node] : ["、", node]));
}

function errors(counts: Record<Kind, number>): ReactNode[] {
  return [
    counts.lacking ? part(counts.lacking, "缺失连接") : null,
    counts.excessive ? part(counts.excessive, "多余连接") : null,
    counts.leaving ? part(counts.leaving, "游离连接") : null,
    counts.reversed ? part(counts.reversed, "方向反转") : null,
  ].filter((node): node is ReactNode => node !== null);
}

export function ScorePanel(props: { counts: Record<Kind, number>; total: number }) {
  const { counts, total } = props;
  const parts = errors(counts);
  return (
    <section className="panel score" aria-labelledby="score-headline">
      <div className="score__figure od-stat">
        <p className="score__value" aria-label={`得分：${total} 条标准命题中连对 ${counts.correct} 条`}>
          {counts.correct}
          <small>/ {total}</small>
        </p>
        <p className="score__caption">
          共 {total} 条标准命题
          <br />
          连对 {counts.correct} 条
        </p>
      </div>
      <div className="score__lede">
        <h2 className="score__headline" id="score-headline">{scoreHeadline(counts, total)}</h2>
        <p className="score__note">
          {parts.length ? (
            <>
              另有 {joined(parts)}。四类错误<strong>不影响分数</strong>，只用来指出改哪里。
            </>
          ) : (
            "这张图和目标图完全一致，没有多余、游离或反转的连接。"
          )}
        </p>
      </div>
    </section>
  );
}
