/** 开发者模式对某个重建的改动：概念、连接词与目标图三块，整份换掉。 */
import type { Concept, Edge, Kit } from "./kit";

export interface Overlay {
  concepts: Concept[];
  connections: string[];
  /** 目标图命题；开发者改图时一起存 */
  target: Edge[];
}

export function applyOverlay(kit: Kit, overlay: Overlay | null): Kit {
  if (!overlay) return kit;
  return {
    ...kit,
    concepts: overlay.concepts,
    connections: overlay.connections,
    target: overlay.target,
  };
}

function tidy(text: string): string {
  return text.trim().replace(/\s+/g, " ");
}

function taken(labels: string[]): Set<string> {
  return new Set(labels.map((label) => label.trim()));
}

/** 新 id 只在开发期用，前缀让它一眼看得出来是加进去的。 */
function freshId(list: Concept[]): string {
  const ids = new Set(list.map((item) => item.id));
  let n = list.length + 1;
  while (ids.has("dev-" + n)) n += 1;
  return "dev-" + n;
}

export function addConcept(
  list: Concept[], label: string,
): { list: Concept[]; id: string } | null {
  const text = tidy(label);
  if (!text || taken(list.map((item) => item.label)).has(text)) return null;
  const id = freshId(list);
  return { list: [...list, { id, label: text }], id };
}

export function renameConcept(list: Concept[], id: string, label: string): Concept[] {
  const hit = list.find((item) => item.id === id);
  if (!hit) return list;
  const text = tidy(label);
  if (!text) return list;
  const others = taken(list.filter((item) => item.id !== id).map((item) => item.label));
  if (others.has(text)) return list;
  return list.map((item) => (item.id === id ? { id, label: text } : item));
}

export function removeConcept(list: Concept[], id: string): Concept[] {
  return list.filter((item) => item.id !== id);
}

export function addConnector(list: string[], word: string): string[] | null {
  const text = tidy(word);
  if (!text || taken(list).has(text)) return null;
  return [...list, text];
}

export function renameConnector(list: string[], from: string, to: string): string[] {
  const text = tidy(to);
  if (!text || !list.includes(from)) return list;
  if (from !== text && taken(list).has(text)) return list;
  return list.map((word) => (word === from ? text : word));
}

export function removeConnector(list: string[], word: string): string[] {
  return list.filter((item) => item !== word);
}

/** 概念或连接词被删掉后，画布上那些连线就不再成立。 */
export function pruneEdges(edges: Edge[], ids: string[], conns: string[]): Edge[] {
  const live = new Set(ids);
  const words = new Set(conns);
  return edges.filter(
    (edge) => live.has(edge.from) && live.has(edge.to) && words.has(edge.conn),
  );
}

export function prunePlaced<T>(
  placed: Record<string, T>, ids: string[],
): Record<string, T> {
  const live = new Set(ids);
  const out: Record<string, T> = {};
  Object.keys(placed).forEach((id) => {
    if (live.has(id)) out[id] = placed[id];
  });
  return out;
}
