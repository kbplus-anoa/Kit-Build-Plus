/** 报告页：先给结论，再给差异图与逐条明细。未冻结的自检不显示目标图。 */
import { useMemo } from "react";

import type { Attempt } from "../data/attempt";
import type { Frame } from "../hooks/useRoute";
import { usePanelStagger } from "../hooks/usePanelStagger";
import { ReportShell } from "./ReportShell";
import { Closing } from "./report/Closing";
import { DetailSection } from "./report/DetailSection";
import { DiffSection } from "./report/DiffSection";
import { HoldPanel } from "./report/HoldPanel";
import { RBar } from "./report/RBar";
import { ScorePanel } from "./report/ScorePanel";
import { TaxonomyGrid } from "./report/TaxonomyGrid";
import { useReportView } from "./report/useReportView";

interface Props {
  frame: Frame;
  record: Attempt;
  onHome: () => void;
  onRevise: (record: Attempt) => void;
}

export function ReportView(props: Props) {
  const { frame, record, onHome, onRevise } = props;
  const state = useReportView(record);
  const stamp = useMemo(() => record.id + ":" + record.edges.length, [record]);
  usePanelStagger("view-report", stamp);

  return (
    <ReportShell id="view-report" frame={frame}>
      <RBar
        attempt={record.attempt}
        mode={record.mode}
        frozen={record.frozen}
        onHome={onHome}
      />
      <HoldPanel hidden={record.frozen} />
      {record.frozen ? <ScorePanel counts={state.counts} total={state.total} /> : null}
      <TaxonomyGrid counts={state.counts} />
      {record.frozen ? <DiffSection state={state} stamp={stamp} layoutKey={record.id} /> : null}
      <DetailSection state={state} title={record.frozen ? "明细" : "你当前连上的命题"} />
      <Closing frozen={record.frozen} onRevise={() => onRevise(record)} />
    </ReportShell>
  );
}
