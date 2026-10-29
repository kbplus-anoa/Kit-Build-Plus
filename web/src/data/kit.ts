/**
 * 当前这份 kit：概念、连接词与目标命题。一次只装一份，换教材就整份换掉。
 * 画布与零件栏靠它把 id 念成字；报告页自带 labels，不读这里。
 * 开发者模式改的是服务端那一批的图，改完再从服务端装回来。
 */
export interface Concept {
  id: string;
  label: string;
}

export interface Edge {
  from: string;
  conn: string;
  to: string;
}

export interface Kit {
  materialId: number;
  material: string;
  mapVersion: string;
  concepts: Concept[];
  connections: string[];
  total: number;
  /** 目标图命题；开发者模式改的就是它，界面用它画目标图 */
  target?: Edge[];
}

let current: Kit | null = null;
const listeners = new Set<() => void>();

export function subscribeKit(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

function bump(): void {
  listeners.forEach((fn) => fn());
}

/** 命题数以实际带出的目标图为准：开发期改过图，条数跟着变。 */
function measured(kit: Kit): Kit {
  if (!kit.target) return kit;
  return { ...kit, total: kit.target.length };
}

/** 装一份新 kit：解析出来的、题库里切来的、开发期改过的，都从这里进。 */
export function setKit(kit: Kit): void {
  current = measured(kit);
  bump();
}

export function getKit(): Kit | null {
  return current;
}

export function concepts(): Concept[] {
  return current?.concepts ?? [];
}

export function connectors(): string[] {
  return current?.connections ?? [];
}

export function labelOf(id: string): string {
  return current?.concepts.find((concept) => concept.id === id)?.label ?? id;
}

export function known(id: string): boolean {
  return Boolean(current?.concepts.some((concept) => concept.id === id));
}
