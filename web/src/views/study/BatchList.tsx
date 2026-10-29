/** 教材的批次：已冻结几张图、哪张在用、切回哪张、再抽一版。 */
import { useEffect, useState } from "react";

import { Notice } from "../../../../ui-share/atoms/Notice";
import { ApiError, api } from "../../api/client";
import type { KitVersionOut } from "../../types/api";

interface Props {
  materialId: number | null;
  onUseVersion: (materialId: number, mapVersion: string) => Promise<void>;
  onRetry: (materialId: number) => Promise<void>;
}

const SOURCE: Record<string, string> = {
  auto: "自动抽",
  adjudicated: "人工裁定",
};

function whenOf(raw: string): string {
  const at = Date.parse(raw);
  if (Number.isNaN(at)) return raw;
  return new Date(at).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function reasonOf(error: unknown): string {
  return error instanceof ApiError || error instanceof Error
    ? error.message
    : "出错了，稍后再试。";
}

function Row(props: {
  row: KitVersionOut;
  busy: boolean;
  onUse: () => void;
}) {
  const { row, busy, onUse } = props;
  return (
    <li className="rb__batchrow">
      <span className="rb__batchver">{row.map_version}</span>
      <span className="rb__batchmeta">
        {SOURCE[row.source] ?? row.source} · {row.total_propositions} 条 ·{" "}
        {whenOf(row.created_at)}
      </span>
      {row.in_use ? (
        <span className="rb__batchon">在用</span>
      ) : (
        <button
          type="button"
          className="rb__batchuse"
          aria-label={"切到 " + row.map_version}
          disabled={busy}
          onClick={onUse}
        >
          {busy ? "切换中…" : "用这一批"}
        </button>
      )}
    </li>
  );
}

export function BatchList(props: Props) {
  const { materialId, onUseVersion, onRetry } = props;
  const [rows, setRows] = useState<KitVersionOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (materialId === null) {
      setRows([]);
      return;
    }
    setLoading(true);
    setError("");
    api
      .kitVersions(materialId)
      .then((out) => setRows(out.versions))
      .catch((err) => setError(reasonOf(err)))
      .finally(() => setLoading(false));
  }, [materialId]);

  async function use(mapVersion: string) {
    if (materialId === null) return;
    setBusy(mapVersion);
    setNote("");
    setError("");
    try {
      await onUseVersion(materialId, mapVersion);
      const out = await api.kitVersions(materialId);
      setRows(out.versions);
      setNote("已切到 " + mapVersion + "，进画布就用这一版。");
    } catch (err) {
      setError(reasonOf(err));
    } finally {
      setBusy("");
    }
  }

  async function retry() {
    if (materialId === null) return;
    setBusy("retry");
    setNote("");
    setError("");
    try {
      await onRetry(materialId);
      const out = await api.kitVersions(materialId);
      setRows(out.versions);
      setNote("新抽了一版，旧批都还在。");
    } catch (err) {
      setError(reasonOf(err));
    } finally {
      setBusy("");
    }
  }

  if (materialId === null) return null;
  return (
    <section className="rb__batch" aria-labelledby="rb-batch-title">
      <h3 className="rb__picktitle rb__picktitle--sub" id="rb-batch-title">
        目标图批次
      </h3>
      {loading ? <p className="rb__status">正在读批次…</p> : null}
      {!loading && rows.length === 0 ? (
        <p className="rb__status">
          这份教材还没建过目标图。进画布会自动抽一版，也可以现在抽。
        </p>
      ) : null}
      <ul className="rb__batchlist">
        {rows.map((row) => (
          <Row
            key={row.map_version}
            row={row}
            busy={busy === row.map_version}
            onUse={() => void use(row.map_version)}
          />
        ))}
      </ul>
      <div className="rb__batchacts">
        <button
          type="button"
          className="btn btn--ghost"
          disabled={busy !== ""}
          onClick={() => void retry()}
        >
          {busy === "retry" ? "抽取中…" : "重抽一版"}
        </button>
        <p className="rb__status">
          {note || "重抽会另起一版，旧批不动；抽崩了就换一版。"}
        </p>
      </div>
      {error ? (
        <Notice tone="error" className="rb__batcherror">
          {error}
        </Notice>
      ) : null}
    </section>
  );
}
