/** 进重建页时选谁：先看是不是改报告，再看是不是刚上传完，最后才是列表第一份。 */
import type { MaterialOut } from "../../types/api";

export interface FlowStart {
  picked: number | null;
  auto: boolean;
}

export function flowStart(
  materials: MaterialOut[],
  seed: number | null,
  fresh: number | null,
): FlowStart {
  if (seed !== null) return { picked: seed, auto: false };
  if (fresh !== null) return { picked: fresh, auto: true };
  const first = materials[0];
  return { picked: first ? first.material_id : null, auto: false };
}
