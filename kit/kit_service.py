import adjudication
import freeze
import split
import store
import targetmap


class KitError(RuntimeError):
    """冻结与拆 kit 的编排错误。"""


def adjudicate(conn, log: adjudication.AdjudicationLog) -> int:
    """保存一批裁定记录，返回条数。驳回项一并留档。"""
    return store.save(conn, log)


def freeze_batch(conn, batch_id: str,
                 map_version: str) -> targetmap.TargetMap:
    """读回批次 → 冻结目标图。不做静默修改，改须换版本。"""
    log = store.load(conn, batch_id)
    return freeze.freeze(log, map_version)


def build_kit(conn, batch_id: str, map_version: str) -> targetmap.Kit:
    """冻结并拆 kit：一次调用拿到学生可见的零件集。"""
    target = freeze_batch(conn, batch_id, map_version)
    return split.split(target)


def load_batch(conn, batch_id: str) -> adjudication.AdjudicationLog:
    return store.load(conn, batch_id)
