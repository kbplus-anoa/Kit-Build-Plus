/** 上传后先给一段解析动画：三步真实阶段加不确定进度条，真解析完再走；取消就整段作废。 */
import { useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import type { Kit } from "../data/kit";
import { VOCAB } from "../data/vocab";
import { initLoadGlobe, stopLoadGlobe } from "../fx/init";
import type { Frame } from "../hooks/useRoute";
import { kitFrom } from "../data/kitSource";

interface Props {
  frame: Frame;
  file: File | null;
  onHome: () => void;
  onDone: (kit: Kit) => void;
}

const LINES = ["AI 正在分解知识", "AI 正在试着连接", "AI 正在抠字眼", "AI 正在试着理解", "AI 去喝了口水", "AI 回到了书桌前"];
const STEPS = ["读文档", "抽概念", "排画布"];
const SLOW_MS = 10000;

function cssMs(name: string, fallback: number): number {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const value = parseFloat(raw);
  if (Number.isNaN(value)) return fallback;
  return raw.includes("ms") ? value : value * 1000;
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "解析失败了，请稍后再试";
}

function slowHint(step: number, elapsed: number): string {
  if (step > 1) return "正在把概念摆到画布上，马上就好。";
  if (elapsed * 1000 < SLOW_MS) return "";
  if (step === 0) return `已经用了 ${elapsed} 秒，正在读这份文件；大 PDF 会慢一些。`;
  return `已经用了 ${elapsed} 秒，正在逐段抽概念；长文档要等一会儿，可以先去做别的，页面会继续。`;
}

export function LoadView(props: Props) {
  const { frame, file } = props;
  const [step, setStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [finished, setFinished] = useState(false);
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
    setStep(0);
    setElapsed(0);
    setFinished(false);
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

    const tick = window.setInterval(() => {
      setElapsed(Math.floor((Date.now() - started) / 1000));
    }, 1000);

    async function run() {
      try {
        const uploaded = await api.upload(target);
        material.current = uploaded.material_id;
        if (cancelled) return;
        setStep(1);
        const auto = await api.kitAuto({
          material_id: uploaded.material_id,
          text: uploaded.text,
          vocab: VOCAB,
        });
        if (cancelled) return;
        completed.current = true;
        setStep(2);
        await new Promise((resolve) => window.setTimeout(resolve, cssMs("--motion-base", 220)));
        if (cancelled) return;
        setFinished(true);
        await new Promise((resolve) => window.setTimeout(resolve, 320));
        if (!cancelled) {
          done.current(kitFrom(auto, uploaded.material_id, uploaded.file_name));
        }
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
      window.clearInterval(tick);
      window.KBPLoadGlobe?.onBeat(() => undefined);
      stopLoadGlobe();
      drop();
    };
  }, [frame.hidden, file]);

  const style = frame.leaving ? { top: frame.leavingTop } : undefined;
  const hint = slowHint(step, elapsed);

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

        {failure ? null : (
          <>
            <div
              className={"load__bar" + (finished ? " is-done" : " is-sweep")}
              role="progressbar"
              aria-label="解析进度：正在进行，完成后结束"
              aria-busy={!finished}
              id="load-bar-wrap"
            >
              <span className="load__bar-fill" id="load-bar" />
            </div>

            <ol className="load__steps">
              {STEPS.map((label, index) => {
                const state = finished || index < step ? "done" : index === step ? "on" : "wait";
                return (
                  <li key={label} className={"load__step load__step--" + state}>
                    <span className="load__step__dot" aria-hidden="true" />
                    {label}
                  </li>
                );
              })}
            </ol>

            <p className="load__foot">{finished ? "画布准备好了，正在打开。" : hint || " "}</p>
          </>
        )}

        <button type="button" className="load__cancel" onClick={props.onHome}>
          {failure ? "返回" : "取消上传"}
        </button>
      </div>
    </div>
  );
}
