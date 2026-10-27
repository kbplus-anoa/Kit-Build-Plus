/**
 * 主题两档，存本机。切换时两帧内关掉过渡——控件晚到比面板更显眼；
 * 三块 canvas 只重绘当前视图中看得见的那块。
 */

import { useCallback, useEffect, useRef, useState } from "react";

import type { View } from "./useRoute";

export type Theme = "dark" | "light";

const STORE_KEY = "kbp-theme";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function stored(): Theme | null {
  try {
    const value = localStorage.getItem(STORE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

export function useTheme(view: View): { theme: Theme; toggle: () => void } {
  const [theme, setTheme] = useState<Theme>(() => stored() ?? systemTheme());
  const first = useRef(true);
  const seen = useRef(view);
  seen.current = view;

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = theme;

    if (first.current) {
      first.current = false;
      requestAnimationFrame(() => window.KBPAurora?.repaint());
      return;
    }

    root.classList.add("theme-switching");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => root.classList.remove("theme-switching"));
    });

    window.KBPAurora?.repaint();
    if (seen.current === "home") window.KBPGlobe?.repaint();
    if (seen.current === "load") window.KBPLoadGlobe?.repaint();
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: light)");
    function onSystem() {
      if (!stored()) setTheme(systemTheme());
    }
    media.addEventListener("change", onSystem);
    return () => media.removeEventListener("change", onSystem);
  }, []);

  const toggle = useCallback(() => {
    setTheme((now) => {
      const next: Theme = now === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(STORE_KEY, next);
      } catch {
        /* 预览环境可能禁掉存储，本次会话的内存值仍然有效 */
      }
      return next;
    });
  }, []);

  return { theme, toggle };
}
