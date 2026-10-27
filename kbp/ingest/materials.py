"""教材登记：一份上传过的文件留一行，重建与提交靠它取 material_id。"""

COLUMNS = "id, file_name, ext, source, chars, created_at"

SCHEMA = """
CREATE TABLE IF NOT EXISTS material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    ext TEXT NOT NULL,
    source TEXT NOT NULL,
    chars INTEGER NOT NULL,
    digest TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_material_digest ON material(digest);
"""


def ensure(conn) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def add_or_get(conn, file_name, ext, source, chars, digest, created_at) -> int:
    """同一份字节只登记一次：内容没变就复用旧 material_id，变了才新开。"""
    row = conn.execute("SELECT id FROM material WHERE digest = ?", (digest,)).fetchone()
    if row is not None:
        return int(row[0])
    cur = conn.execute(
        "INSERT INTO material (file_name, ext, source, chars, digest, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (file_name, ext, source, int(chars), digest, created_at))
    conn.commit()
    return int(cur.lastrowid)


def get(conn, material_id: int):
    return conn.execute(
        "SELECT " + COLUMNS + " FROM material WHERE id = ?",
        (int(material_id),)).fetchone()


def list_all(conn, limit: int = 200):
    """新上传的在前；limit 夹在 1..1000。"""
    size = max(1, min(int(limit), 1000))
    return conn.execute(
        "SELECT " + COLUMNS + " FROM material ORDER BY id DESC LIMIT ?",
        (size,)).fetchall()
