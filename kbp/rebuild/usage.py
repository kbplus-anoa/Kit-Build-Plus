import sqlite3


class SubmissionUsage:
    """实现 contract-share 的 MapUsagePort：查 submitted 表判定版本是否已被用过。

    kit 不 import rebuild，由装配层把本对象注入给 kit。版本号只在教材内唯一，
    别的教材用过 v1 不代表本教材的 v1 被用过，故按教材限定。
    """

    def __init__(self, conn: sqlite3.Connection, material_id: int) -> None:
        self._conn = conn
        self._material_id = material_id

    def is_used(self, map_version: str) -> bool:
        if not map_version:
            return True
        cur = self._conn.execute(
            "SELECT 1 FROM submitted WHERE target_map_version = ?"
            " AND material_id = ? LIMIT 1",
            (map_version, self._material_id))
        return cur.fetchone() is not None


def fingerprint_used(conn: sqlite3.Connection, fingerprint: str) -> bool:
    """该指纹是否已有学生用过；空指纹视为已用，避免误改。"""
    if not fingerprint:
        return True
    cur = conn.execute(
        "SELECT 1 FROM submitted WHERE fingerprint = ? LIMIT 1", (fingerprint,))
    return cur.fetchone() is not None


def lock_versions(conn: sqlite3.Connection,
                  material_id: int) -> tuple[str, ...]:
    """列出该教材已被学生用过的版本，供界面显示。"""
    cur = conn.execute(
        "SELECT DISTINCT target_map_version FROM submitted"
        " WHERE material_id = ? ORDER BY target_map_version", (material_id,))
    return tuple(r[0] for r in cur.fetchall())
