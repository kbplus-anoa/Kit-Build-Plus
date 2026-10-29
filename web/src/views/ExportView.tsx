/** 导出页：按被试、教材、时点筛被试级快照，下载 CSV。只读，不改库里任何记录。 */
import { useState } from "react";

import { Notice } from "../../../ui-share/atoms/Notice";
import { PageHead, SubBar } from "../../../ui-share/layout/SubBar";
import { ApiError, api } from "../api/client";
import type { Frame } from "../hooks/useRoute";
import { usePanelStagger } from "../hooks/usePanelStagger";
import type { MaterialOut } from "../types/api";
import { Preview } from "./export/Preview";
import { ReportShell } from "./ReportShell";

const TIME_POINTS = [
  { value: "pre", label: "前测" },
  { value: "post", label: "后测" },
  { value: "delayed", label: "延迟后测" },
];

interface Props {
  frame: Frame;
  materials: MaterialOut[];
  onHome: () => void;
}

/** 允许「1, 3 7」这类手打写法；空串即不筛，非法片段直接丢掉。 */
function parseIds(raw: string): number[] {
  const seen = new Set<number>();
  for (const token of raw.split(/[\s,，、]+/)) {
    if (!token) continue;
    const value = Number(token);
    if (Number.isInteger(value) && value > 0) seen.add(value);
  }
  return [...seen];
}

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function ExportView(props: Props) {
  const [people, setPeople] = useState("");
  const [materialIds, setMaterialIds] = useState<number[]>([]);
  const [timePoints, setTimePoints] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const picked = parseIds(people).length + materialIds.length + timePoints.length;
  const filter = {
    participantIds: parseIds(people),
    materialIds,
    timePoints,
  };
  usePanelStagger("view-export", picked);

  async function run() {
    setBusy(true);
    setError("");
    setSaved("");
    try {
      const out = await api.exportSubject(filter);
      save(out.blob, out.name);
      setSaved("已导出 " + out.name + "。");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "导出失败，请稍后再试。");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ReportShell id="view-export" frame={props.frame}>
      <SubBar i={0} onHome={props.onHome} badge={picked ? "已筛 " + picked + " 项" : "全部记录"} />
      <PageHead
        i={1}
        title="导出被试级记录。"
        lede="一人一次提交一行，UTF-8 带 BOM，Excel 直接打开不乱码。"
      />
      <section className="panel" aria-labelledby="export-head">
        <h2 className="export__head" id="export-head">
          筛选条件
        </h2>
        <div className="export__field">
          <label className="export__label" htmlFor="export-people">
            被试编号
          </label>
          <input
            className="export__input"
            id="export-people"
            type="text"
            inputMode="numeric"
            placeholder="如 1, 3, 7；留空即全部"
            value={people}
            onChange={(event) => setPeople(event.target.value)}
          />
        </div>

        <div className="export__field">
          <span className="export__label" id="export-materials-label">
            教材
          </span>
          {props.materials.length === 0 ? (
            <p className="export__hint">还没有教材。上传并抽过 kit 的教材会出现在这里。</p>
          ) : (
            <div className="export__chips" role="group" aria-labelledby="export-materials-label">
              {props.materials.map((item) => {
                const on = materialIds.includes(item.material_id);
                return (
                  <button
                    key={item.material_id}
                    type="button"
                    className={"export__chip" + (on ? " export__chip--on" : "")}
                    aria-pressed={on}
                    title={item.file_name}
                    onClick={() => setMaterialIds((list) => toggle(list, item.material_id))}
                  >
                    {item.file_name}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="export__field">
          <span className="export__label" id="export-points-label">
            时点
          </span>
          <div className="export__chips" role="group" aria-labelledby="export-points-label">
            {TIME_POINTS.map((point) => {
              const on = timePoints.includes(point.value);
              return (
                <button
                  key={point.value}
                  type="button"
                  className={"export__chip" + (on ? " export__chip--on" : "")}
                  aria-pressed={on}
                  onClick={() => setTimePoints((list) => toggle(list, point.value))}
                >
                  {point.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="export__acts">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => void run()}
            disabled={busy}
          >
            {busy ? "导出中…" : "导出被试级 CSV"}
          </button>
          <span className="export__hint">23 列，含四类错误计数与抽崩信号原值。</span>
        </div>
        <Preview filter={filter} limit={8} />
        {error ? (
          <Notice tone="error" className="export__error">
            {error}
          </Notice>
        ) : null}
        {saved ? (
          <Notice tone="done" className="export__done">
            {saved}
          </Notice>
        ) : null}
      </section>

      <div className="closing panel">
        <p className="closing__note">导出只读库，不改任何记录；同一批可以反复导。</p>
        <button type="button" className="btn btn--ghost" onClick={props.onHome}>
          返回主页
        </button>
      </div>
    </ReportShell>
  );
}
