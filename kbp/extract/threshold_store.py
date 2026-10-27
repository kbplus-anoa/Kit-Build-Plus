"""抽崩阈值的持久化：单行配置，没有行就是未校准（D08）。

阈值取开发期冻结图四指标的经验分位点；写入时须同时记录基线来源与
样本量，否则读回仍算未校准。这里只存阈值，不存信号原值。
"""

from kbp.contracts.quality import Thresholds

SCHEMA = """
CREATE TABLE IF NOT EXISTS quality_thresholds (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    s1_max REAL,
    s2_min REAL,
    s3_max REAL,
    s4_max_z REAL,
    min_props INTEGER NOT NULL,
    baseline_mean REAL,
    baseline_sd REAL,
    baseline_source TEXT NOT NULL,
    baseline_n INTEGER NOT NULL
);
"""

FIELDS = ("s1_max", "s2_min", "s3_max", "s4_max_z", "min_props",
          "baseline_mean", "baseline_sd", "baseline_source", "baseline_n")


class ThresholdError(ValueError):
    """阈值组不可写入（样本量或来源不合规）。"""


def ensure(conn) -> None:
    conn.executescript(SCHEMA)


def load(conn) -> Thresholds | None:
    """读回阈值组；没写过时返回 None，表示未校准。"""
    cur = conn.execute("SELECT " + ", ".join(FIELDS)
                       + " FROM quality_thresholds WHERE id = 1")
    row = cur.fetchone()
    if row is None:
        return None
    return Thresholds(*row)


def save(conn, thresholds: Thresholds) -> None:
    """整组覆盖写入；不合法时抛 ThresholdError，不动旧行。"""
    reason = check(thresholds)
    if reason:
        raise ThresholdError(reason)
    conn.execute("INSERT OR REPLACE INTO quality_thresholds (id, "
                 + ", ".join(FIELDS) + ") VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 tuple(getattr(thresholds, name) for name in FIELDS))
    conn.commit()


def check(thresholds: Thresholds) -> str:
    """写入前校验：返回空串表示可写。"""
    if thresholds.min_props < 1:
        return "命题数下限须为正整数"
    if thresholds.baseline_n < 0:
        return "基线样本量不能为负"
    if thresholds.baseline_sd is not None and thresholds.baseline_sd < 0:
        return "基线标准差不能为负"
    wanted = None not in (thresholds.s1_max, thresholds.s2_min,
                          thresholds.s3_max, thresholds.s4_max_z)
    if wanted and (not thresholds.baseline_source.strip()
                   or thresholds.baseline_n <= 0):
        return "写入阈值须同时记录基线来源与样本量"
    return ""
