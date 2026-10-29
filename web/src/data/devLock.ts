/** 开发者模式的门：先输密码，开门后记住，关掉就重新锁上。 */
import type { StoreLike } from "./store";

/** 与后端 kbp/api/dev_gate.py 同一串；只挡误触，真正的门在服务端。 */
export const DEV_PASSWORD = "1234321";

const OPEN_KEY = "kbp-dev-open";
const PASS_KEY = "kbp-dev-pass";

export function localStore(): StoreLike | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}

export function passwordOk(text: string): boolean {
  return text === DEV_PASSWORD;
}

export function unlocked(store: StoreLike | null): boolean {
  if (!store) return false;
  try {
    return store.getItem(OPEN_KEY) === "1" && passOf(store) !== "";
  } catch {
    return false;
  }
}

/** 开门时留下的那串密码，落库时后端要再验一遍。 */
export function passOf(store: StoreLike | null): string {
  if (!store) return "";
  try {
    return store.getItem(PASS_KEY) ?? "";
  } catch {
    return "";
  }
}

export function markUnlocked(store: StoreLike | null, password: string): void {
  if (!store) return;
  try {
    store.setItem(OPEN_KEY, "1");
    store.setItem(PASS_KEY, password);
  } catch {
    return;
  }
}

export function markLocked(store: StoreLike | null): void {
  if (!store) return;
  try {
    store.removeItem(OPEN_KEY);
    store.removeItem(PASS_KEY);
  } catch {
    return;
  }
}
