/** 重建页的两步：先选教材与模式，再进画布。 */
import type { MaterialOut } from "../../types/api";
import { PrepareStep } from "./PrepareStep";
import { RebuildStep } from "./RebuildStep";
import type { StudyFlow } from "./useStudyFlow";

interface Props {
  materials: MaterialOut[];
  flow: StudyFlow;
  onFile: (file: File) => void;
  onUseVersion: (materialId: number, mapVersion: string) => Promise<void>;
  onRetryBatch: (materialId: number) => Promise<void>;
}

export function StudyStep(props: Props) {
  const { materials, flow, onFile, onUseVersion, onRetryBatch } = props;
  if (flow.step === "prepare") {
    return (
      <PrepareStep
        materials={materials}
        picked={flow.picked}
        mode={flow.mode}
        onPickDoc={flow.setPicked}
        onMode={flow.setMode}
        onFile={onFile}
        onContinue={flow.enterCanvas}
        onUseVersion={onUseVersion}
        onRetryBatch={onRetryBatch}
      />
    );
  }
  return (
    <RebuildStep
      mode={flow.mode ?? "study"}
      api={flow.api}
      onSave={flow.saveDraft}
      onSubmit={() => flow.setConfirming(true)}
    />
  );
}
