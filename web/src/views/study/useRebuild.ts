/**
 * 重建画布的状态机外壳：把快照与操作接起来，其余都在 rebuildOps。
 * 它不知道对错，只把连线整理成可提交的形状。
 */

import { useCallback, useRef, useState } from "react";

import type { Edge } from "../../data/kit";
import { writeDraft, type Mode } from "./draft";
import { clampAt, type At } from "./model";
import * as ops from "./rebuildOps";
import { EMPTY, type Ctx, type Pair, type Snapshot } from "./rebuildState";

export interface NoticeMsg {
  text: string;
  mark: string;
  seq: number;
}

export function useRebuild() {
  const [snap, setSnap] = useState<Snapshot>(EMPTY);
  const ref = useRef<Snapshot>(EMPTY);
  const seq = useRef(0);
  const [notice, setNotice] = useState<NoticeMsg | null>(null);

  const patch = useCallback((part: Partial<Snapshot>) => {
    ref.current = { ...ref.current, ...part };
    setSnap(ref.current);
  }, []);

  const say = useCallback((text: string, mark = "·") => {
    seq.current += 1;
    setNotice({ text, mark, seq: seq.current });
  }, []);

  const call = useCallback(
    <T,>(run: (ctx: Ctx) => T): T => run({ snap: ref.current, patch, say }),
    [patch, say],
  );

  const put = useCallback((id: string, at?: At) => call((ctx) => ops.put(ctx, id, at)), [call]);
  const settle = useCallback(
    (id: string, x: number, y: number) =>
      call((ctx) => {
        if (!ctx.snap.placed[id]) {
          ops.put(ctx, id, { x, y });
        } else {
          ctx.patch({ placed: { ...ctx.snap.placed, [id]: clampAt(id, x, y) }, dirty: true });
        }
        ops.armConcept(ctx, id, true);
      }),
    [call],
  );
  const armConcept = useCallback(
    (id: string, fromRail = false) => call((ctx) => ops.armConcept(ctx, id, fromRail)),
    [call],
  );
  const armConnector = useCallback(
    (conn: string) => call((ctx) => ops.armConnector(ctx, conn)),
    [call],
  );
  const commit = useCallback(
    (pair: Pair, conn: string) => call((ctx) => ops.commit(ctx, pair, conn)),
    [call],
  );
  const toggleEdge = useCallback((index: number) => call((ctx) => ops.toggleEdge(ctx, index)), [call]);
  const undo = useCallback(() => call((ctx) => ops.undo(ctx)), [call]);
  const removeSelected = useCallback(() => call((ctx) => ops.removeSelected(ctx)), [call]);
  const clearAll = useCallback(() => call((ctx) => ops.clearAll(ctx)), [call]);

  const move = useCallback(
    (id: string, x: number, y: number) => {
      const current = ref.current.placed;
      if (!current[id]) return;
      patch({ placed: { ...current, [id]: { x, y } } });
    },
    [patch],
  );

  const hydrate = useCallback(
    (next: Edge[], layout: Record<string, At>, saved: number | null, changed: boolean) => {
      patch({
        edges: next,
        placed: layout,
        entering: [],
        armed: null,
        armedConn: null,
        pending: null,
        selected: null,
        drawAt: null,
        savedAt: saved,
        dirty: changed,
      });
    },
    [patch],
  );

  const saveDraft = useCallback(
    (mode: Mode) => {
      if (ref.current.locked) return;
      const at = writeDraft(mode, ref.current.placed, ref.current.edges);
      if (at === null) {
        say("当前环境不允许本地保存，请先不要关闭页面。", "!");
        return;
      }
      patch({ savedAt: at, dirty: false });
      say("草稿已保存，下次进来接着做。", "✓");
    },
    [patch, say],
  );

  const onEntered = useCallback(
    (id: string) => patch({ entering: ref.current.entering.filter((item) => item !== id) }),
    [patch],
  );

  const resetArms = useCallback(
    () => patch({ armed: null, armedConn: null, pending: null, selected: null }),
    [patch],
  );
  const blank = useCallback(() => {
    const snap = ref.current;
    if (!snap.armed && !snap.armedConn && !snap.pending && snap.selected === null) return;
    resetArms();
  }, [resetArms]);

  return {
    ...snap,
    notice,
    say,
    put,
    settle,
    armConcept,
    armConnector,
    commit,
    toggleEdge,
    undo,
    removeSelected,
    clearAll,
    move,
    hydrate,
    saveDraft,
    onEntered,
    resetArms,
    blank,
    setLocked: (value: boolean) => patch({ locked: value }),
    setDrawAt: (value: number | null) => patch({ drawAt: value }),
  };
}

export type RebuildApi = ReturnType<typeof useRebuild>;
