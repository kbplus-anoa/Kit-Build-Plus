/**
 * 面板错峰：按下标给可见面板写 --i，入场延迟由 CSS 里的 --stagger-step 决定。
 * 原型 js/report.js 的 restagger 只数当前真的在屏幕上的块，隐藏的不占位。
 */

import { useLayoutEffect } from "react";

export function staggerPanels(id: string): void {
  const node = document.getElementById(id);
  if (!node) return;
  const panels = node.querySelectorAll<HTMLElement>(".panel");
  let index = 0;
  panels.forEach((panel) => {
    if (panel.hidden) return;
    panel.style.setProperty("--i", String(index));
    index += 1;
  });
}

export function usePanelStagger(id: string, stamp: unknown): void {
  useLayoutEffect(() => {
    staggerPanels(id);
  }, [id, stamp]);
}
