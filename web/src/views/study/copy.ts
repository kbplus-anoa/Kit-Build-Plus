/** 重建页的固定文案，措辞沿用原型。 */
export const UPLOAD_NOTE = "支持 PDF、EPUB、TXT";

export const MODES = [
  {
    id: "study" as const,
    name: "学习模式",
    rule: "提交后返回继续修改，直到与目标图一致。",
    tag: "Kit Build 原论文的经典模式",
  },
  {
    id: "quiz" as const,
    name: "测验模式",
    rule: "提交后不可修改。",
    tag: "用于检验掌握情况",
  },
];

export function prepareStatus(name: string | null, mode: boolean): string {
  if (!name) return "请先选择一份教材。";
  return "已选「" + name + "」。" + (mode ? "点击「进入画布」。" : "现在可以选择模式。");
}
