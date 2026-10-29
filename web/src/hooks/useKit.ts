/** 装进画布的那份 kit：首次读教材、切到题库里的某一批、重抽，三条路都落到同一个 adopt。 */
import { useState } from "react";

import { api } from "../api/client";
import { setKit, type Kit } from "../data/kit";
import { VOCAB } from "../data/vocab";
import { kitFrom, kitFromEntry } from "../data/kitSource";

export function useKit(nameOf: (materialId: number) => string) {
  const [kit, setKitState] = useState<Kit | null>(null);

  function adopt(next: Kit) {
    setKit(next);
    setKitState(next);
  }

  /** 同一个词表版本会直接复用库里的目标图。 */
  async function needKit(materialId: number) {
    const text = await api.materialText(materialId);
    const auto = await api.kitAuto({
      material_id: materialId,
      text: text.text,
      vocab: VOCAB,
    });
    adopt(kitFrom(auto, materialId, text.file_name));
  }

  /** 切到题库里已有的某一批：先标投用，再把它那一版零件集装进画布。 */
  async function useVersion(materialId: number, mapVersion: string) {
    await api.kitUse(materialId, mapVersion);
    const out = await api.kitVersion(materialId, mapVersion);
    adopt(kitFromEntry(out, materialId, nameOf(materialId)));
  }

  /** 抽崩了或想换一版：跳过题库复用重抽，旧批留在库里当对照。 */
  async function retryBatch(materialId: number) {
    const text = await api.materialText(materialId);
    const auto = await api.kitAuto({
      material_id: materialId,
      text: text.text,
      vocab: VOCAB,
      retry: true,
    });
    adopt(kitFrom(auto, materialId, text.file_name));
  }

  return { kit, adopt, needKit, useVersion, retryBatch };
}
