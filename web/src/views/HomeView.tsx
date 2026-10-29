/** 首页：极光背景上的标志与三个入口。入场时序照原型，另有一道兜底。 */
import { useEffect, useState } from "react";

import { initGlobe, stopGlobe } from "../fx/init";

interface Props {
  hidden: boolean;
  inView: boolean;
  out: boolean;
  themeLabel: string;
  onToggleTheme: () => void;
  onStudy: () => void;
  onHistory: () => void;
  onExport: () => void;
  onSettings: () => void;
}

const ENTRANCE = { halo: 40, brand: 120, entries: 380 };
const FALLBACK = 1500;

export function HomeView(props: Props) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    void initGlobe();
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (calm) {
      setStage(3);
      return () => stopGlobe();
    }
    const halo = window.setTimeout(() => setStage(1), ENTRANCE.halo);
    const brand = window.setTimeout(() => setStage(2), ENTRANCE.brand);
    const entries = window.setTimeout(() => setStage(3), ENTRANCE.entries);
    const belt = window.setTimeout(() => setStage(3), FALLBACK);
    return () => {
      [halo, brand, entries, belt].forEach((timer) => window.clearTimeout(timer));
      stopGlobe();
    };
  }, []);

  useEffect(() => {
    if (props.hidden) {
      stopGlobe();
      return;
    }
    void initGlobe();
  }, [props.hidden]);

  const cls = "home" + (props.inView ? " view-in" : "") + (props.out ? " home--out" : "");

  return (
    <main className={cls} id="view-home" hidden={props.hidden}>
      <header className="topbar">
        <a
          className={"wordmark" + (stage >= 1 ? " wordmark--in" : "")}
          id="wordmark"
          href="#home"
          onClick={(event) => event.preventDefault()}
        >
          <span className="wordmark__dot" aria-hidden="true" />
          Kit Build <span className="brand__plus">Plus</span>
        </a>
        <div className="topbar__spacer" />
        <button
          type="button"
          className="theme-toggle"
          id="settings-open"
          aria-label="抽取设置：模型名与接口地址"
          onClick={props.onSettings}
        >
          <svg
            className="od-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path
              d={
                "M9.4 4.86L10.29 4.59L10.65 2.39L13.35 2.39L13.71 4.59L14.6 4.86L15.21 5.11" +
                "L16.03 5.55L17.84 4.25L19.75 6.16L18.45 7.97L18.89 8.79L19.14 9.4L19.41 10.29" +
                "L21.61 10.65L21.61 13.35L19.41 13.71L19.14 14.6L18.89 15.21L18.45 16.03L19.75 17.84" +
                "L17.84 19.75L16.03 18.45L15.21 18.89L14.6 19.14L13.71 19.41L13.35 21.61L10.65 21.61" +
                "L10.29 19.41L9.4 19.14L8.79 18.89L7.97 18.45L6.16 19.75L4.25 17.84L5.55 16.03" +
                "L5.11 15.21L4.86 14.6L4.59 13.71L2.39 13.35L2.39 10.65L4.59 10.29L4.86 9.4" +
                "L5.11 8.79L5.55 7.97L4.25 6.16L6.16 4.25L7.97 5.55L8.79 5.11Z"
              }
            />
            <circle cx="12" cy="12" r="3.1" />
          </svg>
          <span className="theme-toggle__label">设置</span>
        </button>
        <button
          type="button"
          className="theme-toggle"
          id="theme-toggle"
          aria-label={"切换到" + props.themeLabel + "模式"}
          onClick={props.onToggleTheme}
        >
          <svg
            className="od-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="4.2" />
            <path d="M12 2.6v2.1M12 19.3v2.1M2.6 12h2.1M19.3 12h2.1M5.4 5.4l1.5 1.5M17.1 17.1l1.5 1.5M18.6 5.4l-1.5 1.5M6.9 17.1l-1.5 1.5" />
          </svg>
          <span className="theme-toggle__label" id="theme-label">{props.themeLabel}</span>
        </button>
      </header>

      <section className="hero" aria-labelledby="brand-name">
        <div className="logo-stage">
          <div
            className={"logo-stage__halo" + (stage >= 1 ? " logo-stage__halo--in" : "")}
            id="halo"
            aria-hidden="true"
          />
          <canvas
            id="globe"
            width="840"
            height="840"
            role="img"
            aria-label="Kit Build Plus 标志：由一个红色节点向外逐跳连接成球面的概念网络。"
          />
        </div>

        <div className={"brand" + (stage >= 2 ? " brand--in" : "")} id="brand">
          <h1 className="brand__name" id="brand-name">
            Kit Build <span className="brand__plus">Plus</span>
          </h1>
          <p className="brand__motto">链接一切知识</p>
        </div>

        <nav
          className={"entries" + (stage >= 3 ? " entries--in" : "")}
          id="entries"
          aria-label="功能入口"
        >
          <button type="button" className="entry entry--primary" id="entry-study" onClick={props.onStudy}>
            <span className="entry__title">开始学习</span>
            <span className="entry__meta">开始 Kit Building</span>
          </button>
          <button type="button" className="entry" id="entry-history" onClick={props.onHistory}>
            <span className="entry__title">历史报告</span>
            <span className="entry__meta">学而时习之</span>
          </button>
          <button type="button" className="entry" id="entry-export" onClick={props.onExport}>
            <span className="entry__title">数据导出</span>
            <span className="entry__meta">被试级 CSV</span>
          </button>
        </nav>
      </section>

      <footer className="home__foot">
        <span className="mono">Kit Build Plus · 2026 AI信息素养大赛</span>
      </footer>
    </main>
  );
}
