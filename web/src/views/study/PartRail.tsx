/** 零件栏：概念与连接词放在这里。点一下放进画布，鼠标拖到画布也能放，手指拎过去也行。 */
import { RailGroup } from "../../../../ui-share/layout/RailGroup";
import { useFinePointer } from "../../../../ui-share/layout/useFinePointer";
import { useDevMode } from "../../data/devMode";
import { concepts, connectors, type Edge } from "../../data/kit";
import { useKitSnapshot } from "../../hooks/useKitSnapshot";
import type { Pt } from "./carry";
import type { At } from "./model";
import { DevPanel } from "./DevPanel";
import { useCarry } from "./useCarry";

interface Props {
  edges: Edge[];
  placed: Record<string, At>;
  armed: string | null;
  armedConn: string | null;
  locked: boolean;
  onConcept: (id: string) => void;
  onDropAt: (id: string, at: Pt | null) => void;
  onConnector: (word: string) => void;
  onKitChange: () => void;
}

export function PartRail(props: Props) {
  useKitSnapshot();
  const fine = useFinePointer();
  const dev = useDevMode();
  const carry = useCarry({ locked: props.locked, onDrop: props.onDropAt });
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
              draggable={fine && !props.locked}
              disabled={props.locked}
              onPointerDown={(event) => carry.start(event, concept.id, concept.label)}
              onClick={() => {
                if (carry.tookClick()) return;
                props.onConcept(concept.id);
              }}
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
      {dev ? <DevPanel onChange={props.onKitChange} /> : null}
      {carry.ghost ? (
        <span
          className="part part--ghost"
          style={{ left: carry.ghost.x, top: carry.ghost.y }}
          aria-hidden="true"
        >
          {carry.ghost.label}
        </span>
      ) : null}
    </aside>
  );
}
