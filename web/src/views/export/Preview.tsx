/** 导出前的预览：表头加前几行，看清楚了再下整份。 */
import { useState } from "react";

import { Notice } from "../../../../ui-share/atoms/Notice";
import { ApiError, api, type ExportFilter } from "../../api/client";
import type { ExportPreviewOut } from "../../types/export";

interface Props {
  filter: ExportFilter;
  limit: number;
}

function reasonOf(error: unknown): string {
  return error instanceof ApiError ? error.message : "预览失败，请稍后再试。";
}

export function Preview(props: Props) {
  const [data, setData] = useState<ExportPreviewOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setBusy(true);
    setError("");
    try {
      setData(await api.exportPreview(props.filter, props.limit));
    } catch (err) {
      setData(null);
      setError(reasonOf(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="export__preview">
      <button
        type="button"
        className="btn btn--ghost"
        onClick={() => void run()}
        disabled={busy}
        aria-describedby="export-preview-note"
      >
        {busy ? "读取中…" : "先看前 " + props.limit + " 行"}
      </button>
      <span className="export__hint" id="export-preview-note">
        预览与下载用同一套列，空单元格在这里显示为 —。
      </span>
      {error ? (
        <Notice tone="error" className="export__error">
          {error}
        </Notice>
      ) : null}
      {data ? (
        <>
          <Notice tone="note" className="export__hint">
            共 {data.total} 行，下面显示前 {data.rows.length} 行。
          </Notice>
          <div className="export__scroll">
            <table className="export__table">
              <thead>
                <tr>
                  {data.header.map((cell) => (
                    <th key={cell} scope="col">
                      {cell}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, line) => (
                  <tr key={line}>
                    {row.map((cell, column) => (
                      <td key={column}>{cell === "" ? "—" : cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </div>
  );
}
