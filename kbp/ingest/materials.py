"""教材登记：一份上传过的文件留一行，重建与提交靠它取 material_id。"""

COLUMNS = "id, file_name, ext, source, chars, created_at, path, ready"

SCHEMA = """
CREATE TABLE IF NOT EXISTS material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    ext TEXT NOT NULL,
    source TEXT NOT NULL,
    chars INTEGER NOT NULL,
    digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    path TEXT NOT NULL DEFAULT '',
    ready INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_material_digest ON material(digest);
"""


def ensure(conn) -> None:
    conn.executescript(SCHEMA)
    have = {row[1] for row in conn.execute("PRAGMA table_info(material)")}
    if "path" not in have:
        conn.execute("ALTER TABLE material ADD COLUMN path TEXT NOT NULL DEFAULT ''")
    if "ready" not in have:
        conn.execute("ALTER TABLE material ADD COLUMN ready INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def add_or_get(conn, file_name, ext, source, chars, digest, created_at,
               path: str = "") -> int:
    """同一份字节只登记一次：内容没变就复用旧 material_id，变了才新开。"""
    row = conn.execute("SELECT id, path FROM material WHERE digest = ?",
                       (digest,)).fetchone()
    if row is not None:
        if path and not row[1]:
            conn.execute("UPDATE material SET path = ? WHERE id = ?",
                         (path, int(row[0])))
            conn.commit()
        return int(row[0])
    cur = conn.execute(
        "INSERT INTO material (file_name, ext, source, chars, digest,"
        " created_at, path) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (file_name, ext, source, int(chars), digest, created_at, path))
    conn.commit()
    return int(cur.lastrowid)


def mark_ready(conn, material_id: int) -> bool:
    """抽成 kit 之后才算可用：只有就绪的教材才会列给学生。"""
    cur = conn.execute("UPDATE material SET ready = 1 WHERE id = ?",
                       (int(material_id),))
    conn.commit()
    return cur.rowcount > 0


def remove(conn, material_id: int):
    """删掉一行并返回它（调用方据此删原文）；不存在返回 None。"""
    row = get(conn, material_id)
    if row is None:
        return None
    conn.execute("DELETE FROM material WHERE id = ?", (int(material_id),))
    conn.commit()
    return row


def get(conn, material_id: int):
    return conn.execute(
        "SELECT " + COLUMNS + " FROM material WHERE id = ?",
        (int(material_id),)).fetchone()


def list_all(conn, limit: int = 200):
    """只列已抽出 kit 的教材，新的在前；limit 夹在 1..1000。"""
    size = max(1, min(int(limit), 1000))
    return conn.execute(
        "SELECT " + COLUMNS + " FROM material WHERE ready = 1"
        " ORDER BY id DESC LIMIT ?", (size,)).fetchall()
