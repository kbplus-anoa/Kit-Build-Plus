import csv
import io

import kbp.contracts.exportcsv

BOM = "\ufeff"
DELIMITER = ","
PRECISION = 8


class ExportError(ValueError):
    """导出数据不合法。"""


def quote(value) -> str:
    """值统一转字符串：空值用空串，小数按固定精度。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:.{PRECISION}f}"
    return str(value)


def to_csv(payload: kbp.contracts.exportcsv.CsvPayload) -> bytes:
    """CsvPayload → UTF-8 带 BOM 的字节流。缺失值用空串。"""
    if payload.encoding != kbp.contracts.exportcsv.UTF8_BOM:
        raise ExportError("编码必须是 UTF-8 带 BOM，Excel for Windows 才能识别")
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=DELIMITER, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(payload.header)
    for row in payload.rows:
        writer.writerow([quote(v) for v in row])
    return (BOM + buf.getvalue()).encode("utf-8")


def check_width(payload: kbp.contracts.exportcsv.CsvPayload) -> None:
    """每行列数必须与表头一致，否则下游按列取会错位。"""
    width = len(payload.header)
    for index, row in enumerate(payload.rows):
        if len(row) != width:
            raise ExportError(f"第 {index + 1} 行列数为 {len(row)}，"
                              f"应为 {width}")
