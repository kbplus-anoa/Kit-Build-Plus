/** 开发者面板：增减改概念、连接词与目标命题，每次改动都写进库。 */
import { useState } from "react";

import {
  addConcept, addConnector, removeConcept, removeConnector, renameConcept,
  renameConnector, type Overlay,
} from "../../data/devKit";
import { getKit, setKit, type Edge } from "../../data/kit";
import { kitFromEntry } from "../../data/kitSource";
import { addTargetEdge, pruneTarget, removeTargetEdge, replaceTargetEdge, targetOf } from "../../data/devTarget";
import { useKitSnapshot } from "../../hooks/useKitSnapshot";
import { commitOverlay } from "./devCommit";
import { Group } from "./DevGroup";
import { TargetEditor } from "./TargetEditor";

interface Props {
  onChange: () => void;
}

function overlayNow(): Overlay {
  const kit = getKit();
  return {
    concepts: kit ? kit.concepts : [],
    connections: kit ? kit.connections : [],
    target: kit ? targetOf(kit) : [],
  };
}

export function DevPanel(props: Props) {
  useKitSnapshot();
  const kit = getKit();
  const [draftConcept, setDraftConcept] = useState("");
  const [draftConn, setDraftConn] = useState("");
  const [editing, setEditing] = useState<Edge | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  if (!kit) return null;

  const target = targetOf(kit);
  const ids = kit.concepts.map((item) => item.id);
  const words = kit.connections;

  /** 改完就落库，再把库里那一份装回来；图不成立时后端拒收，界面不动。 */
  function commit(next: Overlay | null) {
    if (busy) return;
    const prep = next
      ? { ...next, target: pruneTarget(next.target, next.concepts.map((item) => item.id), next.connections) }
      : null;
    void commitOverlay(prep, {
      setBusy,
      onDone: (body) => {
        setKitFrom(body);
        setNote(next ? "已写进库，重新打开还是这样。" : "已回到服务端解析出来的原样。");
        props.onChange();
      },
      onFail: setNote,
    });
  }

  function setKitFrom(body: Parameters<typeof kitFromEntry>[0]) {
    setKit(kitFromEntry(body, kit!.materialId, kit!.material));
  }

  function conceptAdd() {
    const out = addConcept(kit!.concepts, draftConcept);
    if (!out) {
      setNote("概念名不能为空，也不能和已有的重名。");
      return;
    }
    setDraftConcept("");
    commit({ ...overlayNow(), concepts: out.list });
  }

  function conceptRename(id: string, label: string) {
    const next = renameConcept(kit!.concepts, id, label);
    if (next === kit!.concepts) {
      setNote("名字不能为空，也不能和别的概念重名。");
      return;
    }
    commit({ ...overlayNow(), concepts: next });
  }

  function conceptRemove(id: string) {
    commit({ ...overlayNow(), concepts: removeConcept(kit!.concepts, id) });
  }

  function connAdd() {
    const next = addConnector(words, draftConn);
    if (!next) {
      setNote("连接词不能为空，也不能和已有的重名。");
      return;
    }
    setDraftConn("");
    commit({ ...overlayNow(), connections: next });
  }

  function connRename(from: string, to: string) {
    const next = renameConnector(words, from, to);
    if (next === words) {
      setNote("连接词不能为空，也不能和别的重名。");
      return;
    }
    commit({ ...overlayNow(), connections: next });
  }

  function connRemove(word: string) {
    commit({ ...overlayNow(), connections: removeConnector(words, word) });
  }

  /** 加一条，或者把正在改的那一条换成新的三段。 */
  function triple(from: string, conn: string, to: string) {
    const next = editing
      ? replaceTargetEdge(target, ids, words, editing, { from, conn, to })
      : addTargetEdge(target, ids, words, { from, conn, to });
    if (!next) {
      setNote("三段都得是现有的零件，不能自己连自己，也不能和已有的重复。");
      return;
    }
    setEditing(null);
    commit({ ...overlayNow(), target: next });
  }

  function edgeRemove(edge: Edge) {
    if (editing === edge) setEditing(null);
    commit({ ...overlayNow(), target: removeTargetEdge(target, edge) });
  }

  function restore() {
    setEditing(null);
    commit(null);
  }

  return (
    <section className="dev" aria-label="开发者模式">
      <p className="dev__head">
        开发者模式
        <button type="button" className="dev__reset" onClick={restore}>恢复原样</button>
      </p>
      <Group
        title={"概念 " + kit.concepts.length}
        rows={kit.concepts.map((item) => ({
          key: item.id,
          value: item.label,
          onRename: (text) => conceptRename(item.id, text),
          onRemove: () => conceptRemove(item.id),
        }))}
        draft={draftConcept}
        onDraft={setDraftConcept}
        onAdd={conceptAdd}
        addLabel="加概念"
      />
      <Group
        title={"连接词 " + words.length}
        rows={words.map((word) => ({
          key: word,
          value: word,
          onRename: (text) => connRename(word, text),
          onRemove: () => connRemove(word),
        }))}
        draft={draftConn}
        onDraft={setDraftConn}
        onAdd={connAdd}
        addLabel="加连接词"
      />
      <TargetEditor
        edges={target}
        concepts={kit.concepts}
        connections={words}
        editing={editing}
        onEdit={setEditing}
        onSubmit={triple}
        onRemove={edgeRemove}
      />
      <p className="dev__note">{note || "改名、增删与改图都写进库；提交按改后的图校验。"}</p>
    </section>
  );
}
