/** 重建页：先选教材与模式，再进画布；提交前确认一次，测验模式提交即冻结。 */
import { PageHead, SubBar } from "../../../ui-share/layout/SubBar";
import { type Attempt } from "../data/demo";
import type { Frame } from "../hooks/useRoute";
import { usePanelStagger } from "../hooks/usePanelStagger";
import { ReportShell } from "./ReportShell";
import { Holdings } from "./study/Holdings";
import { StudyStep } from "./study/StudyStep";
import { SubmitDialog } from "./study/SubmitDialog";
import { useStudyFlow } from "./study/useStudyFlow";

interface Props {
  frame: Frame;
  docs: string[];
  seed?: Attempt | null;
  records: Attempt[];
  onHome: () => void;
  onFile: (name: string) => void;
  onSubmit: (record: Attempt, replacing: string | null) => void;
  onOpenRecord: (record: Attempt) => void;
}

export function StudyView(props: Props) {
  const { frame, docs, seed, records, onHome, onFile, onSubmit, onOpenRecord } = props;
  const flow = useStudyFlow({ docs, seed, onSubmit });
  usePanelStagger("view-study", flow.step + ":" + records.length);
  const inCanvas = flow.step === "rebuild";
  const badge = inCanvas ? (flow.mode === "quiz" ? "测验模式" : "学习模式") : "重建 / Rebuild";
  return (
    <ReportShell id="view-study" frame={frame}>
      <SubBar i={0} onHome={onHome} badge={badge} live={inCanvas && flow.mode === "quiz"} />
      <PageHead i={1} title="连接概念。" lede="点选两个概念与一个连接词，即可开始连接" />
      <StudyStep docs={docs} flow={flow} onFile={onFile} />
      <Holdings
        records={records.filter((record) => !record.frozen)}
        onOpen={onOpenRecord}
        onRevise={flow.revise}
      />
      <SubmitDialog flow={flow} />
    </ReportShell>
  );
}
