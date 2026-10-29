/** 记着停在哪一页：手机上从文件选择器回来常常整页重载，重载后不该掉回主页。 */
import type { View } from "../hooks/useRoute";

const KEY = "kbp.view";

/** 重载后讲得出来的页。报告与加载页靠一份内存里的记录、一个 File 讲，重载后没得讲，落到上一页。 */
const RESTORE: Partial<Record<View, View>> = {
  study: "study",
  history: "history",
  export: "export",
  load: "study",
  report: "history",
};

export function lastView(): View | null {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    return raw ? RESTORE[raw as View] ?? null : null;
  } catch {
    return null;
  }
}

export function rememberView(view: View): void {
  try {
    if (view === "home") {
      window.sessionStorage.removeItem(KEY);
      return;
    }
    window.sessionStorage.setItem(KEY, view);
  } catch {
    /* 隐私模式写不了，就当没记过 */
  }
}
