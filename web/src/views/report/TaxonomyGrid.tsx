/** 四类差异各自的形状与含义，数量来自这一份图。 */
import { Mark } from "../../../../ui-share/atoms/Mark";
import { LABEL, type Kind } from "../../data/reportText";

const ROWS: { kind: Kind; desc: string }[] = [
  { kind: "lacking", desc: "目标里有，你没连" },
  { kind: "excessive", desc: "两概念都在 kit 里，但不该连" },
  { kind: "leaving", desc: "两端对，连接词错" },
  { kind: "reversed", desc: "两端与连接词都对，方向相反" },
];

export function TaxonomyGrid(props: { counts: Record<Kind, number> }) {
  const { counts } = props;
  return (
    <section className="panel taxonomy" aria-label="差异分类">
      {ROWS.map(({ kind, desc }) => (
        <div className={"tax" + (counts[kind] === 0 ? " tax--zero" : "")} key={kind}>
          <p className="tax__head">
            <span className="mark" data-mark={kind} aria-hidden="true">
              <Mark kind={kind} />
            </span>
            {LABEL[kind]}
          </p>
          <p className="tax__count">{counts[kind]}</p>
          <p className="tax__desc">{desc}</p>
        </div>
      ))}
    </section>
  );
}
