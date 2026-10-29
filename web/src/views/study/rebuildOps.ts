/** 画布上的每一次动作：放进概念、点名两端、连成命题、撤销与清空。 */
import { pruneEdges, prunePlaced } from "../../data/devKit";
import { clampAt, findSlot, labelOf, tripleOf, type At } from "./model";
import type { Ctx, Pair } from "./rebuildState";

export function put(ctx: Ctx, id: string, at?: At): boolean {
  const current = ctx.snap.placed;
  if (current[id]) return false;
  const next = at ? clampAt(id, at.x, at.y) : findSlot(current, id);
  ctx.patch({
    placed: { ...current, [id]: next },
    entering: ctx.snap.entering.includes(id) ? ctx.snap.entering : [...ctx.snap.entering, id],
    dirty: true,
  });
  return true;
}

/** 开发者删了概念或连接词：画布上不再成立的连线与落点一并撤下。 */
/** 开发者删了概念或连接词：画布与目标图里不再成立的连线一并撤下。 */
export function pruneKit(ctx: Ctx, ids: string[], conns: string[]): void {
  const edges = pruneEdges(ctx.snap.edges, ids, conns);
  const placed = prunePlaced(ctx.snap.placed, ids);
  const intact = edges.length === ctx.snap.edges.length
    && Object.keys(placed).length === Object.keys(ctx.snap.placed).length;
  if (intact) return;
  ctx.patch({
    edges, placed, armed: null, pending: null, selected: null, dirty: true,
  });
}

export function commit(ctx: Ctx, pair: Pair, conn: string): void {
  if (!pair || !conn) return;
  const spoken = tripleOf({ ...pair, conn });
  if (pair.from === pair.to) {
    ctx.patch({ pending: null, armed: null });
    ctx.say("一个概念不能连到它自己。", "!");
    return;
  }
  const dup = ctx.snap.edges.some(
    (edge) => edge.from === pair.from && edge.conn === conn && edge.to === pair.to,
  );
  if (dup) {
    ctx.patch({ pending: null });
    ctx.say("这条已经连过了：" + spoken + "。", "!");
    return;
  }
  const next = [...ctx.snap.edges, { from: pair.from, conn, to: pair.to }];
  ctx.patch({
    edges: next,
    drawAt: next.length - 1,
    pending: null,
    armed: null,
    selected: null,
    dirty: true,
  });
  ctx.say("已连成「" + spoken + "」。", "✓");
}

export function armConcept(ctx: Ctx, id: string, fromRail = false): void {
  const snap = ctx.snap;
  if (snap.locked || !snap.placed[id]) return;
  ctx.patch({ selected: null });

  if (snap.armed === id && !fromRail) {
    ctx.patch({ armed: null, pending: null });
    return;
  }
  if (!snap.armed) {
    ctx.patch({ armed: id, pending: null });
    const head = fromRail
      ? "已把「" + labelOf(id) + "」放入画布并选中"
      : "已选中「" + labelOf(id) + "」";
    ctx.say(head + "，再点另一个概念来连接。", fromRail ? "↓" : "＋");
    return;
  }
  if (snap.armed === id) return;

  const pair = { from: snap.armed, to: id };
  ctx.patch({ pending: pair, armed: null });
  if (snap.armedConn) {
    const conn = snap.armedConn;
    ctx.patch({ armedConn: null });
    commit(ctx, pair, conn);
    return;
  }
  ctx.say(
    fromRail
      ? "已把「" + labelOf(id) + "」放进画布：两端选好了，现在选连接词。"
      : "两端选好了，现在选连接词。",
    "→",
  );
}

export function armConnector(ctx: Ctx, conn: string): void {
  const snap = ctx.snap;
  if (snap.locked) return;
  if (snap.pending) {
    commit(ctx, snap.pending, conn);
    return;
  }
  const next = snap.armedConn === conn ? null : conn;
  ctx.patch({ armedConn: next });
  if (next) {
    ctx.say(
      "已选中连接词「" + conn + "」，再点" + (snap.armed ? "一个" : "两个") + "概念即可连成一条命题。",
      "＋",
    );
  }
}

export function toggleEdge(ctx: Ctx, index: number): void {
  const snap = ctx.snap;
  if (snap.locked || !snap.edges[index]) return;
  const next = snap.selected === index ? null : index;
  ctx.patch({ selected: next });
  if (next !== null) ctx.say("已选中这条命题，按 Delete 删除，或再点一次取消选中。", "⌫");
}

export function undo(ctx: Ctx): void {
  const snap = ctx.snap;
  if (snap.locked) return;
  if (!snap.edges.length) {
    ctx.say("还没有可以撤销的连接。", "·");
    return;
  }
  const gone = snap.edges[snap.edges.length - 1];
  ctx.patch({
    edges: snap.edges.slice(0, -1),
    selected: null,
    pending: null,
    drawAt: null,
    dirty: true,
  });
  ctx.say("已撤销「" + tripleOf(gone) + "」。", "↺");
}

export function removeSelected(ctx: Ctx): void {
  const snap = ctx.snap;
  if (snap.locked || snap.selected === null) return;
  const gone = snap.edges[snap.selected];
  ctx.patch({
    edges: snap.edges.filter((_, index) => index !== snap.selected),
    selected: null,
    dirty: true,
  });
  if (gone) ctx.say("已删除「" + tripleOf(gone) + "」。", "⌫");
}

export function clearAll(ctx: Ctx): void {
  const snap = ctx.snap;
  if (snap.locked) return;
  if (!snap.edges.length && !Object.keys(snap.placed).length) return;
  ctx.patch({
    edges: [],
    placed: {},
    selected: null,
    armed: null,
    pending: null,
    dirty: true,
  });
  ctx.say("画布已清空，可以重新开始。", "·");
}
