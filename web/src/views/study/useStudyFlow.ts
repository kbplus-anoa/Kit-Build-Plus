/** 重建页的状态机：选教材、选模式、画布、真提交、存草稿。 */
import { useEffect, useRef, useState } from "react";

import { ApiError, api as backend } from "../../api/client";
import type { Attempt } from "../../data/attempt";
import { getKit, type Kit } from "../../data/kit";
import { CONDITION, PARTICIPANT_ID, TIME_POINT } from "../../data/session";
import type { CurrentDraftIn, DraftOut, MaterialOut, SubmitIn, SubmitOut } from "../../types/api";
import { clearDraft, readDraft, rememberMode, type Mode } from "./draft";
import { flowStart } from "./flowStart";
import { clockOf, seedPlacements } from "./model";
import { useRebuild } from "./useRebuild";

export type Step = "prepare" | "rebuild";

interface Args {
  materials: MaterialOut[];
  seed?: Attempt | null;
  fresh?: number | null;
  onNeedKit: (materialId: number) => Promise<void>;
  onSubmitted: (materialId: number, seq: number, out: SubmitOut) => void;
  onConflict: (materialId: number) => void;
  onDraftSaved: () => void;
}

const MODE_OF: Record<string, "study" | "test"> = { study: "study", quiz: "test" };
const UI_MODE: Record<string, "study" | "quiz"> = { study: "study", test: "quiz" };

export type StudyFlow = ReturnType<typeof useStudyFlow>;

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "出错了，稍后再试。";
}

/** 后端存的当前草稿；没有就当没存过。 */
async function readRemote(materialId: number): Promise<DraftOut | null> {
  try {
    return await backend.currentDraft(PARTICIPANT_ID, materialId, TIME_POINT);
  } catch {
    return null;
  }
}

export function useStudyFlow(args: Args) {
  const start = useRef(
    flowStart(args.materials, args.seed?.materialId ?? null, args.fresh ?? null),
  );
  const [picked, setPicked] = useState<number | null>(start.current.picked);
  const [mode, setMode] = useState<Mode | null>(args.seed?.mode ?? null);
  const [step, setStep] = useState<Step>("prepare");
  const [confirming, setConfirming] = useState(false);
  const [revising, setRevising] = useState<string | null>(null);
  const api = useRebuild();

  const apiRef = useRef(api);
  const modeRef = useRef(mode);
  const saveRef = useRef<() => void>(() => undefined);
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

  async function openMaterial(materialId: number, uiMode: Mode) {
    rememberMode(uiMode);
    setRevising(null);
    try {
      const kit = await ensureKit(materialId);
      if (!kit) return;
      const remote = await readRemote(kit.materialId);
      // 换了批次，旧草稿里的概念 id 就未必还对得上，先认版本号再恢复。
      if (remote && remote.mode === MODE_OF[uiMode] && remote.map_version === kit.mapVersion) {
        const edges = remote.propositions.map((prop) => ({
          from: prop.head_id,
          conn: prop.connection,
          to: prop.tail_id,
        }));
        openCanvas(edges, seedPlacements(edges), Date.parse(remote.saved_at), false);
        api.say("草稿已恢复：" + clockOf(Date.parse(remote.saved_at)) + " 保存的 " + edges.length + " 条命题。", "↺");
        return;
      }
      const draft = readDraft(kit.materialId, kit.mapVersion);
      if (draft && draft.mode === uiMode) {
        openCanvas(draft.edges, draft.placed, draft.at, false);
        api.say("草稿已恢复：" + clockOf(draft.at) + " 保存的 " + draft.edges.length + " 条命题。", "↺");
        return;
      }
      openCanvas([], {}, null, false);
    } catch (error) {
      api.say(messageOf(error), "!");
    }
  }

  async function enterCanvas() {
    if (!mode) return;
    if (picked === null) {
      api.say("先选一份教材。", "!");
      return;
    }
    await openMaterial(picked, mode);
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
      if (error instanceof ApiError && error.status === 409) {
        api.say("这次测验已经提交过了，直接打开当时那份报告。", "·");
        args.onConflict(kit.materialId);
        return;
      }
      api.say(messageOf(error), "!");
      return;
    }
    clearDraft();
    api.hydrate(api.edges, api.placed, null, false);
    if (mode === "quiz") api.setLocked(true);
    args.onSubmitted(kit.materialId, out.submit_seq, out);
  }

  /** 存草稿：本地先落一份，再送后端；后端存不上就只会丢换设备后的恢复。 */
  function saveDraft() {
    if (!mode) return;
    api.saveDraft(mode);
    const kit = getKit();
    if (!kit) return;
    const body: CurrentDraftIn = {
      map_version: kit.mapVersion,
      mode: MODE_OF[mode],
      participant_id: PARTICIPANT_ID,
      material_id: kit.materialId,
      time_point: TIME_POINT,
      propositions: api.edges.map((edge) => ({
        head_id: edge.from,
        connection: edge.conn,
        tail_id: edge.to,
      })),
    };
    void backend
      .saveCurrent(body)
      .then(() => args.onDraftSaved())
      .catch(() => undefined);
  }
  saveRef.current = saveDraft;

  /** 从「继续」栏里的一条草稿直接进画布。 */
  async function resumeDraft(draft: DraftOut) {
    const uiMode = UI_MODE[draft.mode] ?? "study";
    setMode(uiMode);
    setPicked(draft.material_id);
    setRevising(null);
    rememberMode(uiMode);
    try {
      const kit = await ensureKit(draft.material_id);
      if (!kit) return;
      const edges = draft.propositions.map((prop) => ({
        from: prop.head_id,
        conn: prop.connection,
        to: prop.tail_id,
      }));
      openCanvas(edges, seedPlacements(edges), Date.parse(draft.saved_at), false);
    } catch (error) {
      api.say(messageOf(error), "!");
    }
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

  /* 上传刚解析完就带着那份教材进画布：退回选择教材处等于让刚做完的解析白费。 */
  useEffect(() => {
    const opening = start.current;
    if (!opening.auto || opening.picked === null) return;
    setMode("study");
    void openMaterial(opening.picked, "study");
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
        if (modeRef.current) saveRef.current();
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
    revising, api, enterCanvas, submit, saveDraft, revise, resumeDraft,
  };
}
