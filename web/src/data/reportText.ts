/** 报告页的固定文案与判定类别的读法。 */
import type { MarkKind } from "../../../ui-share/atoms/Mark";

export type Kind = MarkKind;

export const LABEL: Record<Kind, string> = {
  correct: "正确",
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
  reversed: "方向反了：目标图里这条LABEL是反过来的",
};

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
