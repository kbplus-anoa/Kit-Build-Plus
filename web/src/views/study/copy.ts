/** 重建页的固定文案，措辞沿用原型。 */
export const UPLOAD_NOTE = "支持 PDF、EPUB、TXT";

export const MODES = [
  {
    id: "study" as const,
    name: "学习模式",
    rule: "提交后可以返回继续改，直到与目标图一致。分数随改动变化，不作为成绩。",
    tag: "可反复修改",
  },
  {
    id: "quiz" as const,
    name: "测验模式",
    rule: "提交后不可修改，这次分数即为成绩。进入前请确认这张图已经连好。",
    tag: "提交后锁定",
  },
];

export function prepareStatus(picked: string | null, mode: boolean): string {
  if (!picked) return "先选一份教材。选定后模式才会解锁。";
  return "已选「" + picked + "」。" + (mode ? "再点「进入画布」。" : "现在可以选一种模式。");
}
