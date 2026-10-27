/** fx 原型脚本是纯 JS，Vite 打包后由 window 暴露控制口。 */
declare module "*.js";

interface AuroraApi {
  repaint: () => void;
  stop: () => void;
  resume: () => void;
}

interface GlobeApi {
  start: (callback?: () => void) => void;
  stop: () => void;
  resume: () => void;
  repaint: () => void;
}

interface LoadGlobeApi {
  start: () => void;
  stop: () => void;
  repaint: () => void;
  onBeat: (fn: (index: number) => void) => void;
}

interface Window {
  KBPAurora?: AuroraApi;
  KBPGlobe?: GlobeApi;
  KBPLoadGlobe?: LoadGlobeApi;
}
