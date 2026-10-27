/** 三个 canvas 脚本都在导入时抓元素，所以必须先有元素再动态导入。 */
const loaded = { aurora: false, globe: false, load: false };

export async function initAurora(): Promise<void> {
  if (loaded.aurora || !document.getElementById("aurora-gl")) return;
  loaded.aurora = true;
  await import("./aurora.js");
}

export async function initGlobe(): Promise<void> {
  if (loaded.globe) {
    window.KBPGlobe?.start();
    return;
  }
  if (!document.getElementById("globe")) return;
  loaded.globe = true;
  await import("./globe.js");
  window.KBPGlobe?.start();
}

export async function initLoadGlobe(): Promise<void> {
  if (loaded.load) {
    window.KBPLoadGlobe?.start();
    return;
  }
  if (!document.getElementById("load-globe")) return;
  loaded.load = true;
  await import("./loadglobe.js");
  window.KBPLoadGlobe?.start();
}

export function stopGlobe(): void {
  window.KBPGlobe?.stop();
}

export function stopLoadGlobe(): void {
  window.KBPLoadGlobe?.stop();
}

export function repaintFx(): void {
  window.KBPAurora?.repaint();
  window.KBPGlobe?.repaint();
  window.KBPLoadGlobe?.repaint();
}
