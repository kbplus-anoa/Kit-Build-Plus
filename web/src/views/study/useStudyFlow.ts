/** 重建页的状态机：选教材、选模式、画布、真提交、存草稿。 */
import { useEffect, useRef, useState } from "react";

import { api as backend } from "../../api/client";
import type { Attempt } from "../../data/attempt";
import { getKit, type Kit } from "../../data/kit";
import { CONDITION, PARTICIPANT_ID, TIME_POINT } from "../../data/session";
import type { MaterialOut, SubmitIn, SubmitOut } from "../../types/api";
import { buildAttempt } from "./attemptBuild";
import { clearDraft, readDraft, rememberMode, type Mode } from "./draft";
import { clockOf } from "./model";
import { useRebuild } from "./useRebuild";

export type Step = "prepare" | "rebuild";

interface Args {
  materials: MaterialOut[];
  seed?: Attempt | null;
  onNeedKit: (materialId: number) => Promise<void>;
  onSubmit: (record: Attempt, replacing: string | null) => void;
}

export type StudyFlow = ReturnType<typeof useStudyFlow>;

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "出错了，稍后再试。";
}

export function useStudyFlow(args: Args) {
  const [picked, setPicked] = useState<number | null>(
    args.seed?.materialId ?? args.materials[0]?.material_id ?? null,
  );
  const [mode, setMode] = useState<Mode | null>(args.seed?.mode ?? null);
  const [step, setStep] = useState<Step>("prepare");
  const [confirming, setConfirming] = useState(false);
  const [revising, setRevising] = useState<string | null>(null);
  const api = useRebuild();

  const apiRef = useRef(api);
  const modeRef = useRef(mode);
  apiRef.current = api;
  modeRef.current = mode;

  function openCanvas(
    edges: Attempt["edges"],
    layout: Record<string, { x: number; y: number }>,
    saved: number | null,
    changed: boolean,
  ) {
    api.hydrate(edges, layout, saved, changed);
    setStep("rebuild");
  }

  /** 画布用的概念与目标命题来自当前教材；没有就先请上层去建。 */
  async function ensureKit(materialId: number | null): Promise<Kit | null> {
    if (materialId === null) {
      api.say("先选一份教材。", "!");
      return null;
    }
    let kit = getKit();
    if (!kit || kit.materialId !== materialId) {
      api.say("正在读这份教材，先建出概念与目标图…", "·");
      try {
        await args.onNeedKit(materialId);
      } catch (error) {
        api.say(messageOf(error) + " 首页右上角「设置」可以填模型与接口地址。", "!");
        return null;
      }
      kit = getKit();
    }
    if (!kit) api.say("这份教材还没能建出目标图，请重新上传。", "!");
    return kit;
  }

  async function enterCanvas() {
    if (!mode) return;
    rememberMode(mode);
    setRevising(null);
    try {
      const kit = await ensureKit(picked);
      if (!kit) return;
      const draft = readDraft(kit.materialId, kit.mapVersion);
      if (draft && draft.mode === mode) {
        openCanvas(draft.edges, draft.placed, draft.at, false);
        api.say("草稿已恢复：" + clockOf(draft.at) + " 保存的 " + draft.edges.length + " 条命题。", "↺");
        return;
      }
      openCanvas([], {}, null, false);
    } catch (error) {
      api.say(messageOf(error), "!");
    }
  }

  async function submit() {
    setConfirming(false);
    if (!mode || picked === null) return;
    if (!api.edges.length) {
      api.say("画布上还没有任何连接，先连一条再提交。", "!");
      return;
    }
    const kit = getKit();
    if (!kit || kit.materialId !== picked) {
      api.say("这份教材的目标图还没准备好，先回到第一步。", "!");
      return;
    }
    const body: SubmitIn = {
      map_version: kit.mapVersion,
      mode: mode === "quiz" ? "test" : "study",
      condition: CONDITION,
      participant_id: PARTICIPANT_ID,
      material_id: kit.materialId,
      time_point: TIME_POINT,
      propositions: api.edges.map((edge) => ({
        head_id: edge.from,
        connection: edge.conn,
        tail_id: edge.to,
      })),
    };
    let out: SubmitOut;
    try {
      out = await backend.submit(body);
    } catch (error) {
      api.say(messageOf(error), "!");
      return;
    }
    const record = buildAttempt(kit, [...api.edges], api.placed, mode, out);
    clearDraft();
    api.hydrate(api.edges, api.placed, null, false);
    if (mode === "quiz") api.setLocked(true);
    args.onSubmit(record, revising);
  }

  function saveDraft() {
    if (mode) api.saveDraft(mode);
  }

  async function revise(record: Attempt) {
    setMode("study");
    setRevising(record.id);
    try {
      const kit = await ensureKit(record.materialId);
      if (!kit) return;
      setPicked(record.materialId);
      openCanvas(record.edges, record.layout, null, true);
    } catch (error) {
      api.say(messageOf(error), "!");
    }
  }

  useEffect(() => {
    if (picked !== null) return;
    const first = args.materials[0];
    if (first) setPicked(first.material_id);
  }, [args.materials, picked]);

  useEffect(() => {
    if (!args.seed) return;
    setMode("study");
    setRevising(args.seed.id);
    apiRef.current.hydrate(args.seed.edges, args.seed.layout, null, true);
    setStep("rebuild");
  }, []);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const view = document.getElementById("view-study");
      if (!view || view.hidden) return;
      if (document.querySelector("dialog[open]")) return;
      const live = apiRef.current;
      const meta = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();
      if (meta && key === "s") {
        event.preventDefault();
        if (modeRef.current) live.saveDraft(modeRef.current);
        return;
      }
      if (meta && event.key === "Enter") {
        event.preventDefault();
        setConfirming(true);
        return;
      }
      if (meta && key === "z") {
        event.preventDefault();
        live.undo();
        return;
      }
      if ((event.key === "Delete" || event.key === "Backspace") && live.selected !== null) {
        event.preventDefault();
        live.removeSelected();
        return;
      }
      if (event.key === "Escape" && (live.pending || live.armed || live.armedConn || live.selected !== null)) {
        event.preventDefault();
        live.resetArms();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    function onLeave(event: BeforeUnloadEvent) {
      const live = apiRef.current;
      if (!live.dirty || live.locked || !live.edges.length) return;
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", onLeave);
    return () => window.removeEventListener("beforeunload", onLeave);
  }, []);

  return {
    picked, setPicked, mode, setMode, step, confirming, setConfirming,
    revising, api, enterCanvas, submit, saveDraft, revise,
  };
}
