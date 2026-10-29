/** 本机存储的类型与兜底：隐私模式或配额满时退回内存语义，页面照常可用。 */

export interface StoreLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export function localStore(): StoreLike | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}
