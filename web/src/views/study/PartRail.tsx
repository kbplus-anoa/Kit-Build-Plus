/** 零件栏：概念与连接词放在这里。点一下放进画布，拖到画布也能放。 */
import { RailGroup } from "../../../../ui-share/layout/RailGroup";
import { concepts, connectors, type Edge } from "../../data/kit";
import type { At } from "./model";

interface Props {
  edges: Edge[];
  placed: Record<string, At>;
  armed: string | null;
  armedConn: string | null;
  locked: boolean;
  onConcept: (id: string) => void;
  onConnector: (word: string) => void;
}

export function PartRail(props: Props) {
  const CONCEPTS = concepts();
  const CONNECTORS = connectors();
  const used = new Set(props.edges.flatMap((edge) => [edge.from, edge.to]));
  const conns = new Set(props.edges.map((edge) => edge.conn));
  const ordered = [...CONCEPTS].sort(
    (a, b) => Number(used.has(a.id)) - Number(used.has(b.id)),
  );
  return (
    <aside className="rail" aria-label="零件栏">
      <p className="rail__count">
        已放入 <b>{Object.keys(props.placed).length}</b> / {CONCEPTS.length} 个概念 ·{" "}
        <b>{conns.size}</b> / {CONNECTORS.length} 种连接词
      </p>
      <RailGroup title="概念" count={Object.keys(props.placed).length} total={CONCEPTS.length}>
        {ordered.map((concept) => {
          const armed = props.armed === concept.id;
          const cls =
            "part" + (props.placed[concept.id] ? " is-placed" : "") + (armed ? " is-armed" : "");
          return (
            <button
              key={concept.id}
              type="button"
              className={cls}
              aria-pressed={armed}
              draggable={!props.locked}
              disabled={props.locked}
              onClick={() => props.onConcept(concept.id)}
              onDragStart={(event) => {
                event.dataTransfer.setData("text/plain", concept.id);
                event.dataTransfer.effectAllowed = "copy";
              }}
            >
              {concept.label}
            </button>
          );
        })}
      </RailGroup>
      <RailGroup title="连接词" count={conns.size} total={CONNECTORS.length}>
        {CONNECTORS.map((word) => {
          const armed = props.armedConn === word;
          return (
            <button
              key={word}
              type="button"
              className={"part part--conn" + (armed ? " is-armed" : "")}
              aria-pressed={armed}
              disabled={props.locked}
              onClick={() => props.onConnector(word)}
            >
              {word}
            </button>
          );
        })}
      </RailGroup>
    </aside>
  );
}
