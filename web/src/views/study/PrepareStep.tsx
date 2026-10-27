/** 第一步：先选教材，再选模式。没有教材时模式是锁着的。 */
import { DocPicker } from "./DocPicker";
import { ModePicker } from "./ModePicker";
import { prepareStatus } from "./copy";

interface Props {
  docs: string[];
  picked: string | null;
  mode: "study" | "quiz" | null;
  onPickDoc: (name: string) => void;
  onMode: (mode: "study" | "quiz") => void;
  onFile: (name: string) => void;
  onContinue: () => void;
}

export function PrepareStep(props: Props) {
  const { docs, picked, mode, onPickDoc, onMode, onFile, onContinue } = props;
  const locked = !picked;
  return (
    <section className="panel" id="rb-pick" aria-labelledby="rb-pick-title">
      <h2 className="rb__picktitle" id="rb-pick-title">选择教材</h2>
      <DocPicker docs={docs} picked={picked} onPick={onPickDoc} onFile={onFile} />
      <h3 className="rb__picktitle rb__picktitle--sub" id="rb-mode-title">选择模式</h3>
      <ModePicker mode={mode} locked={locked} onMode={onMode} />
      <div className="rb__bar" style={{ marginTop: "var(--space-4)", border: 0, padding: 0, background: "transparent" }}>
        <button type="button" className="btn btn--primary" disabled={!picked || !mode} onClick={onContinue}>
          进入画布
        </button>
        <p className="rb__status">{prepareStatus(picked, mode !== null)}</p>
      </div>
    </section>
  );
}
