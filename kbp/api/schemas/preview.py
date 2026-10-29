"""导出预览的回包：表头加前几行，页面上先看一眼再下载。"""
from pydantic import BaseModel, Field


class ExportPreviewOut(BaseModel):
    header: list[str] = Field(description="CSV 表头，与下载文件同一套列名")
    rows: list[list[str]] = Field(description="前几行，行内顺序与表头对齐")
    total: int = Field(description="符合条件的总行数，不受 limit 影响")
