/** 上传后先给一段解析动画：进度封顶 90%，等够了才走；取消就整段作废。 */
import { useEffect, useRef, useState } from "react";

import { initLoadGlobe, stopLoadGlobe } from "../fx/init";
import type { Frame } from "../hooks/useRoute";

interface Props {
  frame: Frame;
  file: string;
  onHome: () => void;
  onDone: (file: string) => void;
}

const LINES = ["AI 正在分解知识", "AI 正在试着连接"];
const CAP = 90;
const STEP_MS = 260;
const HOLD_MS = 2600;

function cssMs(name: string, fallback: number): number {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const value = parseFloat(raw);
  if (Number.isNaN(value)) return fallback;
  return raw.includes("ms") ? value : value * 1000;
}

export function LoadView(props: Props) {
  const { frame, file } = props;
  const [progress, setProgress] = useState(0);
  const [line, setLine] = useState(0);
  const [swap, setSwap] = useState(false);
  const done = useRef(props.onDone);
  done.current = props.onDone;

  useEffect(() => {
    if (frame.hidden || !file) return;
    let cancelled = false;
    setProgress(0);
    setLine(0);
    setSwap(false);

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

    const hold = window.setTimeout(() => {
      if (cancelled) return;
      setProgress(100);
      window.setTimeout(() => {
        if (!cancelled) done.current(file);
      }, cssMs("--motion-base", 220));
    }, HOLD_MS);

    return () => {
      cancelled = true;
      window.clearInterval(step);
      window.clearTimeout(hold);
      window.KBPLoadGlobe?.onBeat(() => undefined);
      stopLoadGlobe();
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
          <p className="load__file" id="load-file">{file}</p>
          <p className={"load__line" + (swap ? " load__line--swap" : "")} id="load-line">
            {LINES[line]}
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
          取消上传
        </button>
      </div>
    </div>
  );
}
