/**
 * 当前这份 kit：概念、连接词与目标命题数。一次只装一份，换教材就整份换掉。
 * 画布与零件栏靠它把 id 念成字；报告页自带 labels，不读这里。
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
}

let current: Kit | null = null;

export function setKit(kit: Kit): void {
  current = kit;
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
