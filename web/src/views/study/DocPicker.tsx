/** 教材选择：上传入口与已上传列表。上传按钮只是外壳，真正接文件的是藏起来的 input。 */
import { useRef, useState } from "react";

import type { MaterialOut } from "../../types/api";
import { UPLOAD_NOTE } from "./copy";

const ALLOWED = ["pdf", "epub", "txt"];

function extOf(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot > 0 ? name.slice(dot + 1).toLowerCase() : "";
}

function UploadIcon() {
  return (
    <svg
      className="od-icon upload__icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 16V4M7 9l5-5 5 5" />
      <path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16" />
    </svg>
  );
}

function DocList(props: {
  materials: MaterialOut[];
  picked: number | null;
  onPick: (id: number) => void;
}) {
  if (props.materials.length === 0) {
    return <span className="doc doc--empty">还没有上传过文档</span>;
  }
  return (
    <>
      {props.materials.map((material) => (
        <button
          key={material.material_id}
          type="button"
          className={"doc" + (props.picked === material.material_id ? " doc--active" : "")}
          aria-pressed={props.picked === material.material_id}
          onClick={() => props.onPick(material.material_id)}
        >
          <span className="doc__name" title={material.file_name}>
            {material.file_name}
          </span>
          <span className="doc__ext">{material.ext}</span>
        </button>
      ))}
    </>
  );
}

export function DocPicker(props: {
  materials: MaterialOut[];
  picked: number | null;
  onPick: (id: number) => void;
  onFile: (file: File) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");

  function accept(list: FileList | null) {
    const file = list?.[0];
    if (!file) return;
    const ext = extOf(file.name);
    if (!ALLOWED.includes(ext)) {
      setError("这个格式暂不支持：「" + (ext || "未知格式") + "」。请上传 PDF、EPUB 或 TXT 文件。");
      return;
    }
    setError("");
    props.onFile(file);
  }

  return (
    <div className="docpick">
      <div className="upload docpick__upload">
        <input
          ref={input}
          className="upload__input"
          id="upload-file"
          type="file"
          accept=".pdf,.epub,.txt,application/pdf,application/epub+zip,text/plain"
          onChange={(event) => {
            accept(event.currentTarget.files);
            event.currentTarget.value = "";
          }}
        />
        <button
          type="button"
          className="upload__btn"
          id="upload-btn"
          onClick={() => input.current?.click()}
        >
          <UploadIcon />
          上传教材
        </button>
        <p className="upload__note">{UPLOAD_NOTE}</p>
        <p className="upload__error" id="upload-error" role="alert" hidden={!error}>
          {error}
        </p>
      </div>
      <div className="doclist" aria-label="已上传的文档">
        <DocList materials={props.materials} picked={props.picked} onPick={props.onPick} />
      </div>
    </div>
  );
}
