/**
 * 六个视图之间的路由：离场、入场、滚动记忆、Esc 返回。
 * 照原型的 show/goHome：动画类写在真实节点上，React 只决定谁还挂着。
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { lastView, rememberView } from "../data/view";

export type View = "home" | "load" | "study" | "report" | "history" | "export";

export const IDS: Record<View, string> = {
  home: "view-home",
  load: "view-load",
  study: "view-study",
  report: "view-report",
  history: "view-history",
  export: "view-export",
};

const FOCUS_MS = 160;
const HOME_OUT_MS = 230;

function tokens(name: string, fallback: number): number {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const value = parseFloat(raw);
  if (Number.isNaN(value)) return fallback;
  return raw.includes("ms") ? value : value * 1000;
}

function calm(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function focusBack(node: HTMLElement) {
  const back = node.querySelector<HTMLElement>(".rbar__back, .subbar__back, .load__cancel");
  if (!back) return;
  const active = document.activeElement;
  if (active && active !== document.body && node.contains(active)) return;
  back.focus();
}

export interface Frame {
  hidden: boolean;
  leaving: boolean;
  leavingTop: number;
}

export interface Route {
  view: View;
  frame: (target: View) => Frame;
  show: (target: View) => void;
  home: () => void;
  homeIn: boolean;
  homeOut: boolean;
}

export function useRoute(initial: View = "home"): Route {
  const [view, setView] = useState<View>(() => lastView() ?? initial);
  const [leaving, setLeaving] = useState<{ view: View; top: number } | null>(null);
  const [homeIn, setHomeIn] = useState(true);
  const [homeOut, setHomeOut] = useState(false);
  const current = useRef<View>(view);
  const fromHome = useRef(true);
  const leaveTimer = useRef(0);
  const homeTimer = useRef(0);
  const focusTimer = useRef(0);
  const scroll = useRef<Partial<Record<View, number>>>({});

  useEffect(() => {
    if (view === "home") return;
    const node = document.getElementById(IDS[view]);
    if (!node) return;
    const root = document.documentElement;
    const entering = fromHome.current;
    fromHome.current = false;

    window.clearTimeout(focusTimer.current);
    window.scrollTo(0, scroll.current[view] ?? 0);

    if (entering) {
      root.classList.remove("report-open");
      void node.offsetWidth;
    }
    const raf = requestAnimationFrame(() => {
      if (current.current !== view) return;
      if (entering) root.classList.add("report-open");
      focusTimer.current = window.setTimeout(() => {
        if (current.current === view) focusBack(node);
      }, FOCUS_MS);
    });
    return () => cancelAnimationFrame(raf);
  }, [view]);

  const show = useCallback((target: View) => {
    const from = current.current;
    if (from === target) return;
    scroll.current[from] = window.scrollY;
    current.current = target;
    fromHome.current = from === "home";
    window.clearTimeout(leaveTimer.current);
    window.clearTimeout(homeTimer.current);
    window.clearTimeout(focusTimer.current);

    window.KBPGlobe?.stop();
    window.KBPAurora?.stop();
    rememberView(target);
    setHomeIn(false);
    setView(target);

    if (from === "home") {
      setLeaving(null);
      if (calm()) return;
      setHomeOut(true);
      homeTimer.current = window.setTimeout(() => setHomeOut(false), HOME_OUT_MS);
      return;
    }

    if (calm()) {
      setLeaving(null);
      return;
    }
    setLeaving({ view: from, top: -window.scrollY });
    leaveTimer.current = window.setTimeout(() => setLeaving(null), tokens("--motion-exit", 190) + 30);
  }, []);

  const home = useCallback(() => {
    const from = current.current;
    if (from === "home") return;
    scroll.current[from] = window.scrollY;
    window.clearTimeout(leaveTimer.current);
    window.clearTimeout(homeTimer.current);
    window.clearTimeout(focusTimer.current);
    setHomeOut(false);

    const finish = () => {
      current.current = "home";
      fromHome.current = false;
      document.documentElement.classList.remove("report-open");
      rememberView("home");
      setView("home");
      setLeaving(null);
      setHomeIn(false);
      window.scrollTo(0, scroll.current.home ?? 0);
      window.KBPGlobe?.repaint();
      window.KBPGlobe?.resume();
      window.KBPAurora?.resume();
      const replay = () => setHomeIn(true);
      if (calm()) replay();
      else requestAnimationFrame(() => requestAnimationFrame(replay));
      window.setTimeout(() => document.getElementById("wordmark")?.focus(), FOCUS_MS);
    };

    if (calm()) {
      finish();
      return;
    }
    setLeaving({ view: from, top: -window.scrollY });
    leaveTimer.current = window.setTimeout(finish, tokens("--motion-exit", 190) + 30);
  }, []);

  const frame = useCallback(
    (target: View): Frame => ({
      hidden: view !== target && leaving?.view !== target,
      leaving: leaving?.view === target,
      leavingTop: leaving?.view === target ? leaving.top : 0,
    }),
    [view, leaving],
  );

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== "Escape" || current.current === "home") return;
      if (event.defaultPrevented) return;
      if (document.querySelector("dialog[open]")) return;
      event.preventDefault();
      home();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [home]);

  useEffect(() => {
    function onHash() {
      const id = location.hash.replace("#", "") as View;
      if (IDS[id] && current.current !== id) show(id);
      else if (!IDS[id] && current.current !== "home") home();
    }
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [show, home]);

  return { view, frame, show, home, homeIn, homeOut };
}
