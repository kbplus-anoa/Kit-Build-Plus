/** 重建页的两步：先选教材与模式，再进画布。 */
import { PrepareStep } from "./PrepareStep";
import { RebuildStep } from "./RebuildStep";
import type { StudyFlow } from "./useStudyFlow";

interface Props {
  docs: string[];
  flow: StudyFlow;
  onFile: (name: string) => void;
}

export function StudyStep(props: Props) {
  const { docs, flow, onFile } = props;
  if (flow.step === "prepare") {
    return (
      <PrepareStep
        docs={docs}
        picked={flow.picked}
        mode={flow.mode}
        onPickDoc={flow.setPicked}
        onMode={flow.setMode}
        onFile={onFile}
        onContinue={flow.enterCanvas}
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
