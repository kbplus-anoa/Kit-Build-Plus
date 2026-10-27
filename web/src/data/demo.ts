/**
 * 示例数据：教材「认知心理学 · 记忆系统」的概念、六条目标命题与三条记录。
 * 字段与判定口径照原型 data.js，接后端后形状按 KitAutoOut / SubmitOut 留位。
 */

import type { MarkKind } from "../../../ui-share/atoms/Mark";

export type Kind = MarkKind;

export interface Concept {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface Edge {
  from: string;
  conn: string;
  to: string;
}

export const CONNECTORS = ["进入", "经过", "转入", "依赖", "发生", "导致"];

const COLS = [95, 250, 405, 560, 715, 870];
const ROWS = [70, 190, 330, 460];

function layout(labels: string[]): Concept[] {
  return labels.map((label, i) => ({
    id: label,
    label,
    x: COLS[i % 6],
    y: ROWS[Math.floor(i / 6)],
  }));
}

export const CONCEPTS = layout([
  "注意", "工作记忆", "组块", "精细复述", "机械复述", "提取",
  "保持", "编码", "系列位置效应", "长时记忆", "干扰", "消退",
  "感觉记忆", "短时记忆", "复述", "再认", "遗忘", "回忆",
  "情景记忆", "语义记忆", "程序性记忆", "内隐记忆", "近因效应", "首因效应",
]);

export const TARGET: Edge[] = [
  { from: "感觉记忆", conn: "进入", to: "短时记忆" },
  { from: "短时记忆", conn: "经过", to: "复述" },
  { from: "复述", conn: "转入", to: "长时记忆" },
  { from: "短时记忆", conn: "依赖", to: "编码" },
  { from: "长时记忆", conn: "发生", to: "遗忘" },
  { from: "遗忘", conn: "导致", to: "复述" },
];

const triple = (edge: Edge) => edge.from + "\u0000" + edge.conn + "\u0000" + edge.to;
const pair = (edge: Edge) => edge.from + "\u0000" + edge.to;

const EXPECTED = TARGET.map(triple);
const REVERSED = new Set(TARGET.map((t) => t.to + "\u0000" + t.conn + "\u0000" + t.from));
const PAIRS = new Set(TARGET.map(pair));

/** 先判方向反转，再判两端对连接词错；两端与连接词全错才算多余。 */
export function classify(edges: Edge[]): Map<number, Kind> {
  const out = new Map<number, Kind>();
  edges.forEach((edge, i) => {
    if (EXPECTED.includes(triple(edge))) out.set(i, "correct");
    else if (REVERSED.has(triple(edge))) out.set(i, "reversed");
    else if (PAIRS.has(pair(edge))) out.set(i, "leaving");
    else out.set(i, "excessive");
  });
  return out;
}

/** 目标里有、学生整条没连上的命题。 */
export function missing(edges: Edge[]): Edge[] {
  const given = new Set(edges.map(triple));
  return TARGET.filter((target) => !given.has(triple(target)));
}

export function tally(edges: Edge[]): Record<Kind, number> {
  const counts: Record<Kind, number> = {
    correct: 0, lacking: 0, excessive: 0, leaving: 0, reversed: 0,
  };
  for (const kind of classify(edges).values()) counts[kind] += 1;
  counts.lacking = missing(edges).length;
  return counts;
}

export const LABEL: Record<Kind, string> = {
  correct: "连对",
  lacking: "缺失连接",
  excessive: "多余连接",
  leaving: "游离连接",
  reversed: "方向反转",
};

export const LEGEND_DESC: Record<Kind, string> = {
  correct: "与目标图完全一致",
  lacking: "目标里有，你没连 · 虚线",
  excessive: "这对概念之间不该有连接 · 加粗实线",
  leaving: "两端对，连接词错 · 波浪线",
  reversed: "与目标方向相反 · 双向箭头",
};

export const NOTE: Record<Kind, string> = {
  correct: "与目标图一致",
  lacking: "目标图里有这条，你的图上没有",
  excessive: "这两个概念之间没有这条连接",
  leaving: "两端是对的，连接词不对",
  reversed: "方向反了：目标图里这条是反过来的",
};

export interface Attempt {
  id: string;
  material: string;
  mode: "study" | "quiz";
  attempt: string;
  when: string;
  frozen: boolean;
  edges: Edge[];
}

export const RECORDS: Attempt[] = [
  {
    id: "demo-3",
    material: "认知心理学 · 记忆系统",
    mode: "quiz",
    attempt: "第 3 次",
    when: "今天 15:42",
    frozen: true,
    edges: [
      { from: "感觉记忆", conn: "进入", to: "短时记忆" },
      { from: "短时记忆", conn: "经过", to: "复述" },
      { from: "复述", conn: "转入", to: "长时记忆" },
      { from: "短时记忆", conn: "依赖", to: "编码" },
      { from: "复述", conn: "经过", to: "短时记忆" },
      { from: "短时记忆", conn: "发生", to: "编码" },
      { from: "编码", conn: "依赖", to: "复述" },
    ],
  },
  {
    id: "demo-2",
    material: "认知心理学 · 记忆系统",
    mode: "quiz",
    attempt: "第 2 次",
    when: "今天 15:18",
    frozen: true,
    edges: [
      { from: "感觉记忆", conn: "进入", to: "短时记忆" },
      { from: "短时记忆", conn: "经过", to: "复述" },
      { from: "复述", conn: "转入", to: "长时记忆" },
      { from: "感觉记忆", conn: "经过", to: "短时记忆" },
    ],
  },
  {
    id: "demo-1",
    material: "认知心理学 · 记忆系统",
    mode: "study",
    attempt: "第 1 次",
    when: "昨天 20:05",
    frozen: false,
    edges: [
      { from: "感觉记忆", conn: "进入", to: "短时记忆" },
      { from: "短时记忆", conn: "经过", to: "复述" },
      { from: "复述", conn: "转入", to: "长时记忆" },
      { from: "短时记忆", conn: "依赖", to: "编码" },
      { from: "遗忘", conn: "导致", to: "复述" },
    ],
  },
];

export function scoreHeadline(counts: Record<Kind, number>, total: number): string {
  if (counts.correct === total && counts.excessive + counts.leaving + counts.reversed === 0) {
    return `全部 ${total} 条都连对了，而且没有多余、游离或反转的连接。`;
  }
  const parts = [`你连对了 ${counts.correct} 条`];
  if (counts.lacking) parts.push(`漏了 ${counts.lacking} 条`);
  if (counts.excessive) parts.push(`${counts.excessive} 条多余`);
  if (counts.leaving) parts.push(`${counts.leaving} 条游离`);
  if (counts.reversed) parts.push(`${counts.reversed} 条方向反了`);
  return parts.join("，") + "。";
}
