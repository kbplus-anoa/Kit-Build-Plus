/** 导出预览的回包：表头加前几行，行内顺序与表头对齐。 */
export interface ExportPreviewOut {
  header: string[];
  rows: string[][];
  total: number;
}
