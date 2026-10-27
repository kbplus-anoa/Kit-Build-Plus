/** 第二步：画布本体。模式在进来时就锁定，画布从不说对错。 */
import { useEffect, useState } from "react";

import type { RebuildApi } from "./useRebuild";
import { CanvasStage } from "./CanvasStage";
import { ConnectorChooser } from "./ConnectorChooser";
import { PartRail } from "./PartRail";
import { RebuildBar } from "./RebuildBar";

interface Props {
  mode: "study" | "quiz";
  api: RebuildApi;
  onSave: () => void;
  onSubmit: () => void;
}

/** 选完模式换到画布，给自己一段短入场，而不是硬切。 */
function useStepEnter(): boolean {
  const [enter, setEnter] = useState(false);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setEnter(true));
    return () => cancelAnimationFrame(frame);
  }, []);
  return enter;
}

export function RebuildStep(props: Props) {
  const { mode, api } = props;
  const enter = useStepEnter();
  const open = Boolean(api.pending);

  function fromRail(id: string) {
    if (api.placed[id]) api.armConcept(id);
    else {
      api.put(id);
      api.armConcept(id, true);
    }
  }

  return (
    <section className={"panel" + (enter ? " is-enter" : "")} id="rb-work">
      <div className="rb">
        <PartRail
          edges={api.edges}
          placed={api.placed}
          armed={api.armed}
          armedConn={api.armedConn}
          locked={api.locked}
          onConcept={fromRail}
          onConnector={api.armConnector}
        />
        <CanvasStage
          placed={api.placed}
          edges={api.edges}
          notice={api.notice}
          entering={api.entering}
          armed={api.armed}
          locked={api.locked}
          selected={api.selected}
          drawAt={api.drawAt}
          onConcept={api.armConcept}
          onEntered={api.onEntered}
          onPlaced={api.settle}
          onEdge={api.toggleEdge}
          onMove={api.move}
          onBlank={api.blank}
          onDrawn={() => api.setDrawAt(null)}
        />
        <RebuildBar
          mode={mode}
          locked={api.locked}
          edges={api.edges}
          savedAt={api.savedAt}
          dirty={api.dirty}
          onUndo={api.undo}
          onClear={api.clearAll}
          onSave={props.onSave}
          onSubmit={props.onSubmit}
        />
        <ConnectorChooser
          open={open}
          armedConn={api.armedConn}
          onPick={api.armConnector}
        />
      </div>
    </section>
  );
}
