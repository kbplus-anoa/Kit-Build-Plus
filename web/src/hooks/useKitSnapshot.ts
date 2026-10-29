/** 订阅当前 kit：开发者改了概念或连接词，画布与零件栏跟着重画。 */
import { useSyncExternalStore } from "react";

import { getKit, subscribeKit } from "../data/kit";

export function useKitSnapshot() {
  return useSyncExternalStore(subscribeKit, getKit, getKit);
}
