/** 上传后先给一段解析动画：进度封顶 90%，真解析完再走；取消就整段作废。 */
import { useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import type { Kit } from "../data/kit";
import { VOCAB } from "../data/vocab";
import { initLoadGlobe, stopLoadGlobe } from "../fx/init";
import type { Frame } from "../hooks/useRoute";
import { kitFrom } from "./study/attemptBuild";

interface Props {
  frame: Frame;
  file: File | null;
  onHome: () => void;
  onDone: (kit: Kit) => void;
}

const LINES = ["AI 正在分解知识", "AI 正在试着连接", "AI 正在抠字眼", "AI 正在试着理解", "AI 去喝了口水", "AI 回到了书桌前"];
const CAP = 90;
const STEP_MS = 260;
const MIN_MS = 1200;

function cssMs(name: string, fallback: number): number {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const value = parseFloat(raw);
  if (Number.isNaN(value)) return fallback;
  return raw.includes("ms") ? value : value * 1000;
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "解析失败了，请稍后再试。";
}

export function LoadView(props: Props) {
  const { frame, file } = props;
  const [progress, setProgress] = useState(0);
  const [line, setLine] = useState(0);
  const [swap, setSwap] = useState(false);
  const [failure, setFailure] = useState("");
  const done = useRef(props.onDone);
  const busy = useRef<File | null>(null);
  const material = useRef<number | null>(null);
  const completed = useRef(false);
  done.current = props.onDone;

  useEffect(() => {
    if (frame.hidden || !file || busy.current === file) return;
    const target = file;
    busy.current = target;
    let cancelled = false;
    setProgress(0);
    setLine(0);
    setSwap(false);
    setFailure("");
    const started = Date.now();

    void initLoadGlobe().then(() => {
      if (cancelled) return;
      window.KBPLoadGlobe?.onBeat((index) => {
        setSwap(true);
        window.setTimeout(() => {
          if (cancelled) return;
          setLine(index % LINES.length);
          setSwap(false);
        }, cssMs("--motion-fast", 150));
      });
    });

    const step = window.setInterval(() => {
      setProgress((value) => Math.min(CAP, value + Math.max(1, (CAP - value) * 0.06)));
    }, STEP_MS);

    async function run() {
      try {
        const uploaded = await api.upload(target);
        material.current = uploaded.material_id;
        const auto = await api.kitAuto({
          material_id: uploaded.material_id,
          text: uploaded.text,
          vocab: VOCAB,
        });
        if (cancelled) return;
        completed.current = true;
        const wait = Math.max(0, MIN_MS - (Date.now() - started));
        window.setTimeout(() => {
          if (cancelled) return;
          setProgress(100);
          window.setTimeout(() => {
            if (!cancelled) {
              done.current(kitFrom(auto, uploaded.material_id, uploaded.file_name));
            }
          }, cssMs("--motion-base", 220));
        }, wait);
      } catch (error) {
        busy.current = null;
        drop();
        if (!cancelled) setFailure(messageOf(error));
      }
    }

    function drop() {
      const id = material.current;
      material.current = null;
      if (id !== null && !completed.current) {
        void api.removeMaterial(id).catch(() => undefined);
      }
    }

    void run();

    return () => {
      cancelled = true;
      window.clearInterval(step);
      window.KBPLoadGlobe?.onBeat(() => undefined);
      stopLoadGlobe();
      drop();
    };
  }, [frame.hidden, file]);

  const style = frame.leaving ? { top: frame.leavingTop } : undefined;
  const pct = Math.round(progress);

  return (
    <div
      className={"report load" + (frame.leaving ? " is-leaving" : "")}
      id="view-load"
      hidden={frame.hidden}
      style={style}
    >
      <div className="report__veil" aria-hidden="true" />
      <div className="load__inner">
        <div className="load__stage">
          <canvas
            className="load__globe"
            id="load-globe"
            role="img"
            aria-label="加载中的 Kit Build Plus 标志：概念节点组成的球面，红色原点向外扩散的涟漪表示解析正在进行。"
          />
        </div>

        <div className="load__copy" aria-live="polite">
          <p className="load__file" id="load-file">{file ? file.name : ""}</p>
          <p className={"load__line" + (swap ? " load__line--swap" : "")} id="load-line">
            {failure || LINES[line]}
          </p>
        </div>

        <div
          className="load__bar"
          role="progressbar"
          aria-label="解析进度"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={pct}
          id="load-bar-wrap"
        >
          <span className="load__bar-fill" id="load-bar" style={{ transform: `scaleX(${progress / 100})` }} />
        </div>

        <button type="button" className="load__cancel" onClick={props.onHome}>
          {failure ? "返回" : "取消上传"}
        </button>
      </div>
    </div>
  );
}
