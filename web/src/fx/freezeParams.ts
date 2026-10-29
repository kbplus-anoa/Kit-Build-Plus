/** 冻结参数的判定：纯函数，给 fx 脚本和测试共用。 */
export interface Params {
  get(name: string): string | null;
}

export function paramsOf(search: string): Params {
  const query = search.indexOf("?") === 0 ? search.slice(1) : search;
  const map = new URLSearchParams(query);
  return { get: (name) => map.get(name) };
}

const ON = ["freeze", "static", "still"];

function hit(params: Params, name: string): boolean {
  const raw = params.get(name);
  if (raw === null) return false;
  return ON.indexOf(raw.trim().toLowerCase()) >= 0;
}

export function freezeRequested(params: Params): boolean {
  return hit(params, "fx") || hit(params, "veil");
}

export function urlFreeze(): boolean {
  try {
    return freezeRequested(paramsOf(window.location.search));
  } catch (err) {
    return false;
  }
}
