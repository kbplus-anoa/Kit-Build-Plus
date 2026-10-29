/** 第一步：先选教材，再选模式。没有教材时模式是锁着的。 */
import type { MaterialOut } from "../../types/api";
import { BatchList } from "./BatchList";
import { DocPicker } from "./DocPicker";
import { ModePicker } from "./ModePicker";
import { prepareStatus } from "./copy";

interface Props {
  materials: MaterialOut[];
  picked: number | null;
  mode: "study" | "quiz" | null;
  onPickDoc: (id: number) => void;
  onMode: (mode: "study" | "quiz") => void;
  onFile: (file: File) => void;
  onContinue: () => void;
  onUseVersion: (materialId: number, mapVersion: string) => Promise<void>;
  onRetryBatch: (materialId: number) => Promise<void>;
}

export function PrepareStep(props: Props) {
  const {
    materials, picked, mode, onPickDoc, onMode, onFile, onContinue,
    onUseVersion, onRetryBatch,
  } = props;
  const locked = picked === null;
  const name = materials.find((item) => item.material_id === picked)?.file_name ?? null;
  return (
    <section className="panel" id="rb-pick" aria-labelledby="rb-pick-title">
      <h2 className="rb__picktitle" id="rb-pick-title">选择教材</h2>
      <DocPicker materials={materials} picked={picked} onPick={onPickDoc} onFile={onFile} />
      <BatchList
        materialId={picked}
        onUseVersion={onUseVersion}
        onRetry={onRetryBatch}
      />
      <h3 className="rb__picktitle rb__picktitle--sub" id="rb-mode-title">选择模式</h3>
      <ModePicker mode={mode} locked={locked} onMode={onMode} />
      <div className="rb__bar" style={{ marginTop: "var(--space-4)", border: 0, padding: 0, background: "transparent" }}>
        <button type="button" className="btn btn--primary" disabled={locked || !mode} onClick={onContinue}>
          进入画布
        </button>
        <p className="rb__status">{prepareStatus(name, mode !== null)}</p>
      </div>
    </section>
  );
}
