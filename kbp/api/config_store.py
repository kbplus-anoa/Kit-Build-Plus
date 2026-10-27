"""抽取配置的持久化：一行一条，进程内共用同一个库。

路由层不直接写 SQL，表结构与读写都在这里，方便别处注入 :memory: 库测试。
"""

import kbp.contracts.extractconfig

SCHEMA = """
CREATE TABLE IF NOT EXISTS extract_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    base_url TEXT NOT NULL,
    timeout_s INTEGER NOT NULL,
    max_chars INTEGER NOT NULL,
    enabled INTEGER NOT NULL,
    reasoning_effort TEXT NOT NULL DEFAULT ''
);
"""

FIELDS = ("provider", "model", "base_url", "timeout_s", "max_chars", "enabled",
          "reasoning_effort")


def ensure(conn) -> None:
    conn.executescript(SCHEMA)
    have = {row[1] for row in conn.execute("PRAGMA table_info(extract_config)")}
    if "reasoning_effort" not in have:
        conn.execute("ALTER TABLE extract_config ADD COLUMN"
                     " reasoning_effort TEXT NOT NULL DEFAULT ''")
    conn.commit()


def load(conn):
    """读回已保存的一行；未保存过时返回 None。"""
    cur = conn.execute("SELECT " + ", ".join(FIELDS)
                       + " FROM extract_config WHERE id = 1")
    return cur.fetchone()


def to_config(row) -> kbp.contracts.extractconfig.ExtractConfig:
    """把库里的一行还原成配置；历史的供应商值归一到当前枚举。"""
    return kbp.contracts.extractconfig.ExtractConfig(
        provider=kbp.contracts.extractconfig.canonical_provider(row[0]),
        model=row[1], base_url=row[2], timeout_s=row[3], max_chars=row[4],
        enabled=bool(row[5]), reasoning_effort=row[6] or "")


def load_config(conn) -> kbp.contracts.extractconfig.ExtractConfig:
    """读配置：库里保存过就用库（界面覆盖），否则读 .env 的 KBP_EXTRACT_*。"""
    row = load(conn)
    if row is None:
        import os

        import kbp.api.envfile
        kbp.api.envfile.reload()
        return kbp.contracts.extractconfig.from_env(os.environ)
    return to_config(row)


def save(conn, fields: tuple) -> None:
    conn.execute("INSERT OR REPLACE INTO extract_config (id, "
                 + ", ".join(FIELDS) + ") VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
                 tuple(fields))
    conn.commit()
