/** 重建页的状态机：选教材、选模式、画布、确认、存草稿。 */
import { useEffect, useRef, useState } from "react";

import { type Attempt } from "../../data/demo";
import { clearDraft, readDraft, rememberMode, type Mode } from "./draft";
import { clockOf, seedPlacements } from "./model";
import { useRebuild } from "./useRebuild";

export type Step = "prepare" | "rebuild";

interface Args {
  docs: string[];
  seed?: Attempt | null;
  onSubmit: (record: Attempt, replacing: string | null) => void;
}

export type StudyFlow = ReturnType<typeof useStudyFlow>;

export function useStudyFlow(args: Args) {
  const [picked, setPicked] = useState<string | null>(args.seed?.material ?? args.docs[0] ?? null);
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

  function enterCanvas() {
    if (!mode) return;
    rememberMode(mode);
    setRevising(null);
    const draft = readDraft();
    if (draft && draft.mode === mode) {
      openCanvas(draft.edges, draft.placed, draft.at, false);
      api.say("草稿已恢复：" + clockOf(draft.at) + " 保存的 " + draft.edges.length + " 条命题。", "↺");
      return;
    }
    openCanvas([], {}, null, false);
  }

  function submit() {
    setConfirming(false);
    if (!mode || !picked) return;
    if (!api.edges.length) {
      api.say("画布上还没有任何连接，先连一条再提交。", "!");
      return;
    }
    const record: Attempt = {
      id: "local-" + Date.now(),
      material: picked,
      mode,
      attempt: "本次提交",
      when: "刚刚",
      frozen: mode === "quiz",
      edges: [...api.edges],
    };
    clearDraft();
    api.hydrate(api.edges, api.placed, null, false);
    if (mode === "quiz") api.setLocked(true);
    args.onSubmit(record, revising);
  }

  function saveDraft() {
    if (mode) api.saveDraft(mode);
  }

  function revise(record: Attempt) {
    setMode("study");
    setRevising(record.id);
    openCanvas(record.edges, seedPlacements(record.edges), null, true);
  }

  useEffect(() => {
    if (!args.seed) return;
    setMode("study");
    setRevising(args.seed.id);
    const edges = args.seed.edges;
    apiRef.current.hydrate(edges, seedPlacements(edges), null, true);
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
