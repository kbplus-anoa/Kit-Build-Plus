import sqlite3


class SubmissionUsage:
    """实现 contract-share 的 MapUsagePort：查 submitted 表判定版本是否已被用过。

    kit 不 import rebuild，由装配层把本对象注入给 kit。
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def is_used(self, map_version: str) -> bool:
        if not map_version:
            return True
        cur = self._conn.execute(
            "SELECT 1 FROM submitted WHERE target_map_version = ? LIMIT 1",
            (map_version,))
        return cur.fetchone() is not None


def lock_versions(conn: sqlite3.Connection) -> tuple[str, ...]:
    """列出已被学生用过的全部版本，供管理端展示。"""
    cur = conn.execute(
        "SELECT DISTINCT target_map_version FROM submitted"
        " ORDER BY target_map_version")
    return tuple(r[0] for r in cur.fetchall())
