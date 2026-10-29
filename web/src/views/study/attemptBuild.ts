/** 把一次提交的接口回包拼成报告页要的 Attempt：标签、坐标、目标图都固化下来。 */
import { CHIP_H, chipWidth } from "../../../../ui-share/canvas/geometry";
import type { Attempt } from "../../data/attempt";
import type { Edge, Kit } from "../../data/kit";
import type { RecordOut, SubmitOut } from "../../types/api";
import { VIEW_H, VIEW_W, findSlot, type At } from "./model";

export function labelsOf(kit: Kit): Record<string, string> {
  const labels: Record<string, string> = {};
  kit.concepts.forEach((concept) => {
    labels[concept.id] = concept.label;
  });
  return labels;
}

/** 没放进画布的概念也要有个位置，报告里画全图才不缺人。 */
export function layoutOf(kit: Kit, placed: Record<string, At>): Record<string, At> {
  const out: Record<string, At> = { ...placed };
  kit.concepts.forEach((concept) => {
    if (!out[concept.id]) out[concept.id] = findSlot(out, concept.id);
  });
  return out;
}

/** 后端记录的默认摆位：按零件顺序铺成 6 列，学生自己拖过的位置另存。 */
function gridLayout(concepts: { concept_id: string; label: string }[]): Record<string, At> {
  const out: Record<string, At> = {};
  concepts.forEach((concept, index) => {
    const col = index % 6;
    const row = Math.floor(index / 6);
    const half = chipWidth(concept.label) / 2;
    const x = 100 + col * 152;
    const y = 80 + row * 112;
    out[concept.concept_id] = {
      x: Math.min(VIEW_W - half - 4, Math.max(half + 4, x)),
      y: Math.min(VIEW_H - CHIP_H / 2 - 4, Math.max(CHIP_H / 2 + 4, y)),
    };
  });
  return out;
}

function whenOf(iso: string): string {
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return "刚刚";
  const pad = (value: number) => String(value).padStart(2, "0");
  return (
    pad(at.getMonth() + 1) + "-" + pad(at.getDate()) + " " + pad(at.getHours()) + ":" + pad(at.getMinutes())
  );
}

function edgesOf(props: { head_id: string; connection: string; tail_id: string }[]): Edge[] {
  return props.map((prop) => ({ from: prop.head_id, conn: prop.connection, to: prop.tail_id }));
}

/** 后端的记录：刷新、换设备或重新打开时，报告页都从这份重建。 */
export function attemptFromRecord(record: RecordOut, material: string): Attempt {
  const labels: Record<string, string> = {};
  record.concepts.forEach((concept) => {
    labels[concept.concept_id] = concept.label;
  });
  return {
    id: "srv-" + record.material_id + "-" + record.submit_seq,
    materialId: record.material_id,
    material,
    mapVersion: record.map_version,
    mode: record.mode === "test" ? "quiz" : "study",
    attempt: "第 " + record.submit_seq + " 次",
    when: whenOf(record.submitted_at),
    frozen: record.mode === "test",
    edges: edgesOf(record.propositions),
    target: edgesOf(record.target_propositions),
    errors: record.errors,
    labels,
    layout: gridLayout(record.concepts),
    total: record.total_propositions,
    correct: record.correct_propositions,
    fms: record.fms,
  };
}

export function buildAttempt(
  kit: Kit,
  edges: Edge[],
  placed: Record<string, At>,
  mode: "study" | "quiz",
  out: SubmitOut,
): Attempt {
  return {
    id: "local-" + Date.now(),
    materialId: kit.materialId,
    material: kit.material,
    mapVersion: kit.mapVersion,
    mode,
    attempt: "本次提交",
    when: "刚刚",
    frozen: mode === "quiz",
    edges,
    target: out.target_propositions.map((prop) => ({
      from: prop.head_id,
      conn: prop.connection,
      to: prop.tail_id,
    })),
    errors: out.errors,
    labels: labelsOf(kit),
    layout: layoutOf(kit, placed),
    total: out.total_propositions,
    correct: out.correct_propositions,
    fms: out.fms,
  };
}
