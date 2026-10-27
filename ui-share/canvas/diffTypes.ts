/** 差异图的两种数据形状：一条判定，与图上的筛选。 */
import type { MarkKind } from "../atoms/Mark";

export interface DiffItem {
  from: string;
  to: string;
  conn: string;
  kind: MarkKind;
}

export type DiffFilter = "all" | "error" | "correct";
