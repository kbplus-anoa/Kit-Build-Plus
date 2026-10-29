/** 后端的两份列表：已提交的记录与未冻结的草稿。记录拉不到时退回本地缓存。 */
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Attempt } from "../data/attempt";
import { readRecords, writeRecords } from "../data/records";
import { PARTICIPANT_ID } from "../data/session";
import type { DraftOut } from "../types/api";
import { attemptFromRecord } from "../views/study/attemptBuild";

export function useAttempts(nameOf: (materialId: number) => string) {
  const [records, setRecords] = useState<Attempt[]>(() => readRecords());
  const [drafts, setDrafts] = useState<DraftOut[]>([]);

  /** 记录只以后端为准；本地缓存只在拉不到时兜底。 */
  async function refreshRecords(): Promise<Attempt[]> {
    try {
      const out = await api.records(PARTICIPANT_ID);
      const remote = out.items.map((item) => attemptFromRecord(item, nameOf(item.material_id)));
      remote.sort((left, right) => right.when.localeCompare(left.when));
      setRecords(remote);
      return remote;
    } catch {
      return readRecords();
    }
  }

  async function refreshDrafts() {
    try {
      const out = await api.drafts(PARTICIPANT_ID);
      setDrafts(out.items);
    } catch {
      setDrafts([]);
    }
  }

  useEffect(() => {
    writeRecords(records);
  }, [records]);

  return { records, drafts, refreshRecords, refreshDrafts };
}
