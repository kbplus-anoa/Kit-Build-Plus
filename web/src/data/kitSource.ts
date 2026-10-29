/** 接口回包 → 画布用的 kit：概念、连接词、目标图与命题数都在这里对齐。 */
import type { Kit, Edge } from "./kit";
import type { KitAutoOut, KitOut } from "../types/api";

function edgesOf(props: { head_id: string; connection: string; tail_id: string }[]): Edge[] {
  return props.map((prop) => ({ from: prop.head_id, conn: prop.connection, to: prop.tail_id }));
}

/** 题库里某一批的零件集也是这个形状，切批、首次抽取与开发期改图共用一份拼装。 */
export function kitFromEntry(out: KitOut, materialId: number, material: string): Kit {
  const target = edgesOf(out.propositions);
  return {
    materialId,
    material,
    mapVersion: out.map_version,
    concepts: out.concepts.map((concept) => ({ id: concept.concept_id, label: concept.label })),
    connections: out.connections,
    total: target.length,
    target,
  };
}

export function kitFrom(auto: KitAutoOut, materialId: number, material: string): Kit {
  return kitFromEntry(auto, materialId, material);
}
