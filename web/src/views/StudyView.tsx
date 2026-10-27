/** 重建页：先选教材与模式，再进画布；提交前确认一次，测验模式提交即冻结。 */
import { PageHead, SubBar } from "../../../ui-share/layout/SubBar";
import type { Attempt } from "../data/attempt";
import type { DraftOut, MaterialOut, SubmitOut } from "../types/api";
import type { Frame } from "../hooks/useRoute";
import { usePanelStagger } from "../hooks/usePanelStagger";
import { ReportShell } from "./ReportShell";
import { Holdings } from "./study/Holdings";
import { StudyStep } from "./study/StudyStep";
import { SubmitDialog } from "./study/SubmitDialog";
import { useStudyFlow } from "./study/useStudyFlow";

interface Props {
  frame: Frame;
  materials: MaterialOut[];
  total: number;
  seed?: Attempt | null;
  records: Attempt[];
  drafts: DraftOut[];
  onHome: () => void;
  onFile: (file: File) => void;
  onNeedKit: (materialId: number) => Promise<void>;
  onSubmitted: (materialId: number, seq: number, out: SubmitOut) => void;
  onConflict: (materialId: number) => void;
  onDraftSaved: () => void;
  onOpenRecord: (record: Attempt) => void;
}

export function StudyView(props: Props) {
  const {
    frame, materials, total, seed, records, drafts, onHome, onFile, onNeedKit,
    onSubmitted, onConflict, onDraftSaved, onOpenRecord,
  } = props;
  const flow = useStudyFlow({ materials, seed, onNeedKit, onSubmitted, onConflict, onDraftSaved });
  usePanelStagger("view-study", flow.step + ":" + records.length + ":" + drafts.length);
  const inCanvas = flow.step === "rebuild";
  // 继续栏里同一份教材只留最近一次未冻结的重建，旧的看历史报告。
  const continued: Attempt[] = [];
  const seen = new Set<number>();
  records.forEach((record) => {
    if (record.frozen || seen.has(record.materialId)) return;
    seen.add(record.materialId);
    continued.push(record);
  });
  const badge = inCanvas ? (flow.mode === "quiz" ? "测验模式" : "学习模式") : "重建 / Rebuild";
  return (
    <ReportShell id="view-study" frame={frame}>
      <SubBar i={0} onHome={onHome} badge={badge} live={inCanvas && flow.mode === "quiz"} />
      <PageHead i={1} title="连接概念。" lede="点选两个概念与一个连接词，即可开始连接" />
      <StudyStep materials={materials} flow={flow} onFile={onFile} />
      <Holdings
        records={continued}
        drafts={drafts}
        onOpen={onOpenRecord}
        onRevise={flow.revise}
        onResume={(draft) => void flow.resumeDraft(draft)}
      />
      <SubmitDialog flow={flow} total={total} />
    </ReportShell>
  );
}
