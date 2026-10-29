export type DeviceMode = "mobile" | "desktop";

const KEY = "kbp.device";
const PHONE = /Android|iPhone|iPad|iPod|Windows Phone|HarmonyOS|Mobile/i;

function asked(): DeviceMode | "auto" | null {
  const raw = new URLSearchParams(window.location.search).get("device");
  if (!raw) return null;
  const value = raw.trim().toLowerCase();
  if (value === "mobile" || value === "phone") return "mobile";
  if (value === "desktop" || value === "pc") return "desktop";
  if (value === "auto") return "auto";
  return null;
}

function kept(): DeviceMode | null {
  try {
    const value = window.sessionStorage.getItem(KEY);
    return value === "mobile" || value === "desktop" ? value : null;
  } catch {
    return null;
  }
}

function keep(mode: DeviceMode | null): void {
  try {
    if (mode) window.sessionStorage.setItem(KEY, mode);
    else window.sessionStorage.removeItem(KEY);
  } catch {
    return;
  }
}

function guessed(): DeviceMode {
  const ua = window.navigator.userAgent;
  const pad = /Macintosh/.test(ua) && window.navigator.maxTouchPoints > 1;
  return pad || PHONE.test(ua) ? "mobile" : "desktop";
}

export function deviceMode(): DeviceMode {
  const want = asked();
  if (want === "auto") {
    keep(null);
    return guessed();
  }
  if (want) {
    keep(want);
    return want;
  }
  return kept() ?? guessed();
}

export function applyDevice(): DeviceMode {
  const mode = deviceMode();
  document.documentElement.dataset.device = mode;
  return mode;
}
