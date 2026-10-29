/* 外部冻结开关，判定在 freezeParams（有测试），这里只读地址栏。
 * 冻结时挂一个 window.__kbpFrozen 给测量架，让它知道画面已停在确定的一帧。 */
import { urlFreeze } from "./freezeParams";

export function freezeRequested() {
  const on = urlFreeze();
  if (on) window.__kbpFrozen = true;
  return on;
}
