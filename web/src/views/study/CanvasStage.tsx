/** 画布本体与它的即时提示。 */
import { RebuildCanvas } from "../../../../ui-share/canvas/RebuildCanvas";
import { CONCEPTS, type Edge } from "../../data/demo";
import { Notice } from "./Notice";
import type { At } from "./model";
import type { NoticeMsg } from "./useRebuild";

interface Props {
  placed: Record<string, At>;
  edges: Edge[];
  notice: NoticeMsg | null;
  entering: string[];
  armed: string | null;
  locked: boolean;
  selected: number | null;
  drawAt: number | null;
  onConcept: (id: string) => void;
  onEntered: (id: string) => void;
  onPlaced: (id: string, x: number, y: number) => void;
  onEdge: (index: number) => void;
  onMove: (id: string, x: number, y: number) => void;
  onBlank: () => void;
  onDrawn: () => void;
}

export function CanvasStage(props: Props) {
  return (
    <div className="rb__stage">
      <div className="rb__field">
        <RebuildCanvas
          concepts={CONCEPTS}
          placed={props.placed}
          edges={props.edges}
          entering={props.entering}
          armedId={props.armed}
          locked={props.locked}
          selected={props.selected}
          drawAt={props.drawAt}
          onConcept={props.onConcept}
          onEntered={props.onEntered}
          onPlaced={props.onPlaced}
          onEdge={props.onEdge}
          onMove={props.onMove}
          onBlank={props.onBlank}
          onDrawn={props.onDrawn}
        />
      </div>
      <Notice notice={props.notice} />
    </div>
  );
}
