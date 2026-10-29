/** fx 原型脚本是纯 JS，Vite 打包后由 window 暴露控制口。 */
declare module "*.js";

interface AuroraApi {
  repaint: () => void;
  stop: () => void;
  resume: () => void;
  freeze: () => void;
}

interface GlobeApi {
  start: (callback?: () => void) => void;
  stop: () => void;
  resume: () => void;
  repaint: () => void;
  freeze: () => void;
}

interface LoadGlobeApi {
  start: () => void;
  stop: () => void;
  repaint: () => void;
  onBeat: (fn: (index: number) => void) => void;
  freeze: () => void;
}

interface Window {
  /** 测量架读：fx 是否已停在确定的一帧 */
  __kbpFrozen?: boolean;
  KBPAurora?: AuroraApi;
  KBPGlobe?: GlobeApi;
  KBPLoadGlobe?: LoadGlobeApi;
}
