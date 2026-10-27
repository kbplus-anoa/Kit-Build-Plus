/** 把一次提交的接口回包拼成报告页要的 Attempt：标签、坐标、目标图都固化下来。 */
import type { Attempt } from "../../data/attempt";
import type { Edge, Kit } from "../../data/kit";
import type { KitAutoOut, SubmitOut } from "../../types/api";
import { findSlot, type At } from "./model";

export function kitFrom(auto: KitAutoOut, materialId: number, material: string): Kit {
  return {
    materialId,
    material,
    mapVersion: auto.map_version,
    concepts: auto.concepts.map((concept) => ({ id: concept.concept_id, label: concept.label })),
    connections: auto.connections,
    total: auto.total_propositions,
  };
}

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
