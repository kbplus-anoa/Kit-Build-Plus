/** 画布快照：一次渲染要看的一切，以及与操作函数之间的接口。 */
import type { Edge } from "../../data/kit";
import type { At } from "./model";

export interface Pair {
  from: string;
  to: string;
}

export interface Snapshot {
  edges: Edge[];
  placed: Record<string, At>;
  entering: string[];
  armed: string | null;
  armedConn: string | null;
  pending: Pair | null;
  selected: number | null;
  drawAt: number | null;
  dirty: boolean;
  savedAt: number | null;
  locked: boolean;
}

export const EMPTY: Snapshot = {
  edges: [],
  placed: {},
  entering: [],
  armed: null,
  armedConn: null,
  pending: null,
  selected: null,
  drawAt: null,
  dirty: false,
  savedAt: null,
  locked: false,
};

export interface Ctx {
  snap: Snapshot;
  patch(part: Partial<Snapshot>): void;
  say(text: string, mark?: string): void;
}
