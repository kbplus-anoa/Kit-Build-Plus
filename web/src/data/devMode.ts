/** 开发者模式的开关：只存本机，界面靠订阅跟着变。 */
import { useSyncExternalStore } from "react";

import type { StoreLike } from "./store";

const KEY = "kbp-dev-mode";

function storage(): StoreLike | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}

export function parseFlag(raw: string | null): boolean {
  return raw === "1";
}

export function readFlag(store: StoreLike | null): boolean {
  if (!store) return false;
  try {
    return parseFlag(store.getItem(KEY));
  } catch {
    return false;
  }
}

export function writeFlag(store: StoreLike | null, on: boolean): void {
  if (!store) return;
  try {
    store.setItem(KEY, on ? "1" : "0");
  } catch {
    /* 配额满或隐私模式：开关退回本次会话，不影响页面 */
  }
}

let on = readFlag(storage());
const listeners = new Set<() => void>();

export function devOn(): boolean {
  return on;
}

export function subscribeDev(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

export function setDev(next: boolean): void {
  if (next === on) return;
  on = next;
  writeFlag(storage(), next);
  listeners.forEach((fn) => fn());
}

export function toggleDev(): void {
  setDev(!on);
}

export function useDevMode(): boolean {
  return useSyncExternalStore(subscribeDev, devOn, devOn);
}
