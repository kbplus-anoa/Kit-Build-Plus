/** 目标图编辑：列出当前目标命题，可改可删；底部三段选出新的那一条。 */
import { useEffect, useState } from "react";

import type { Concept, Edge } from "../../data/kit";

interface Props {
  edges: Edge[];
  concepts: Concept[];
  connections: string[];
  editing: Edge | null;
  onEdit: (edge: Edge | null) => void;
  onSubmit: (from: string, conn: string, to: string) => void;
  onRemove: (edge: Edge) => void;
}

const EMPTY: [string, string, string] = ["", "", ""];

function labelOf(concepts: Concept[], id: string): string {
  return concepts.find((item) => item.id === id)?.label ?? id;
}

export function TargetEditor(props: Props) {
  const [draft, setDraft] = useState<[string, string, string]>(EMPTY);
  const editing = props.editing;

  useEffect(() => {
    setDraft(editing ? [editing.from, editing.conn, editing.to] : EMPTY);
  }, [editing]);

  const [from, conn, to] = draft;

  function pick(index: number, value: string) {
    setDraft((old) => {
      const next: [string, string, string] = [old[0], old[1], old[2]];
      next[index] = value;
      return next;
    });
  }

  return (
    <div className="dev__group">
      <p className="dev__title">{"目标图 " + props.edges.length}</p>
      <ul className="dev__edges">
        {props.edges.map((edge) => {
          const on = editing === edge;
          return (
            <li
              className={"dev__edge" + (on ? " is-editing" : "")}
              key={edge.from + ">" + edge.conn + ">" + edge.to}
            >
              <button
                type="button"
                className="dev__triple"
                aria-label={"改这条命题 " + edge.conn}
                onClick={() => props.onEdit(on ? null : edge)}
              >
                {labelOf(props.concepts, edge.from)}
                <b className="dev__conn">{edge.conn}</b>
                {labelOf(props.concepts, edge.to)}
              </button>
              <button
                type="button"
                className="dev__del"
                aria-label={"删除目标命题 " + edge.conn}
                onClick={() => props.onRemove(edge)}
              >
                ✕
              </button>
            </li>
          );
        })}
        {props.edges.length ? null : <li className="dev__empty">目标图是空的。</li>}
      </ul>

      <div className="dev__triplepick">
        <select
          className="dev__select"
          aria-label="起端概念"
          value={from}
          onChange={(event) => pick(0, event.target.value)}
        >
          <option value="">起端</option>
          {props.concepts.map((item) => (
            <option key={item.id} value={item.id}>{item.label}</option>
          ))}
        </select>
        <select
          className="dev__select"
          aria-label="连接词"
          value={conn}
          onChange={(event) => pick(1, event.target.value)}
        >
          <option value="">连接词</option>
          {props.connections.map((word) => (
            <option key={word} value={word}>{word}</option>
          ))}
        </select>
        <select
          className="dev__select"
          aria-label="末端概念"
          value={to}
          onChange={(event) => pick(2, event.target.value)}
        >
          <option value="">末端</option>
          {props.concepts.map((item) => (
            <option key={item.id} value={item.id}>{item.label}</option>
          ))}
        </select>
        <button
          type="button"
          className="dev__addbtn"
          onClick={() => props.onSubmit(from, conn, to)}
        >
          {editing ? "存这条" : "加命题"}
        </button>
        {editing ? (
          <button type="button" className="dev__cancel" onClick={() => props.onEdit(null)}>
            取消
          </button>
        ) : null}
      </div>
    </div>
  );
}
