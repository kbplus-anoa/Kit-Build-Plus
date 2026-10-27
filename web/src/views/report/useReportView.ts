/** 报告页的数据：判定清单、四类计数、筛选与选中。 */
import { useMemo, useState } from "react";

import type { DiffFilter, DiffItem } from "../../../../ui-share/canvas/diffTypes";
import { conceptsOf, countsOf, itemsOf, type Attempt } from "../../data/attempt";
import type { Kind } from "../../data/reportText";

export interface FilterOption {
  id: DiffFilter;
  label: string;
  count: number;
}

function visibility(items: DiffItem[], filter: DiffFilter) {
  const hidden = new Set<number>();
  let shown = 0;
  items.forEach((item, index) => {
    if (visibleOf(item.kind, filter)) shown += 1;
    else hidden.add(index);
  });
  return { hidden, shown };
}

function visibleOf(kind: Kind, filter: DiffFilter): boolean {
  if (filter === "correct") return kind === "correct";
  if (filter === "error") return kind !== "correct";
  return true;
}

function options(total: number, counts: Record<Kind, number>): FilterOption[] {
  return [
    { id: "all", label: "全部", count: total },
    { id: "error", label: "只看差异", count: total - counts.correct },
    { id: "correct", label: "只看连对", count: counts.correct },
  ];
}

export function useReportView(record: Attempt) {
  const [filter, setFilter] = useState<DiffFilter>("all");
  const [selected, setSelected] = useState<number | null>(null);
  const all = useMemo(() => itemsOf(record), [record]);
  const items = useMemo(
    () => (record.frozen ? all : all.filter((item) => item.kind !== "lacking")),
    [all, record.frozen],
  );
  const counts = useMemo(() => countsOf(record), [record]);
  const concepts = useMemo(() => conceptsOf(record), [record]);
  const { hidden, shown } = visibility(items, filter);
  const filters = options(all.length, counts);
  return {
    all, items, counts, concepts, total: record.total,
    filter, setFilter, selected, setSelected, hidden, shown, filters,
  };
}

export type ReportState = ReturnType<typeof useReportView>;
