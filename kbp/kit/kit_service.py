import kbp.contracts.adjudication
import kbp.contracts.extraction
import kbp.kit.freeze
import kbp.kit.split
import kbp.kit.store
import kbp.contracts.targetmap
import kbp.contracts.triple


class KitError(RuntimeError):
    """冻结与拆 kit 的编排错误。"""


def adjudicate(conn, log: kbp.contracts.adjudication.AdjudicationLog) -> int:
    """保存一批裁定记录，返回条数。驳回项一并留档。"""
    return kbp.kit.store.save(conn, log)


def freeze_batch(conn, batch_id: str,
                 map_version: str) -> kbp.contracts.targetmap.TargetMap:
    """读回批次 → 冻结目标图。不做静默修改，改须换版本。"""
    log = kbp.kit.store.load(conn, batch_id)
    return kbp.kit.freeze.freeze(log, map_version)


def build_kit(conn, batch_id: str, map_version: str) -> kbp.contracts.targetmap.Kit:
    """冻结并拆 kit：一次调用拿到学生可见的零件集。"""
    target = freeze_batch(conn, batch_id, map_version)
    return kbp.kit.split.split(target)


def load_batch(conn, batch_id: str) -> kbp.contracts.adjudication.AdjudicationLog:
    return kbp.kit.store.load(conn, batch_id)


def build_kit_auto(result: kbp.contracts.triple.ExtractionResult,
                   map_version: str):
    # 返回 (TargetMap, Kit)：运行期自动路一次拿到目标图与学生零件集
    """运行期自动路：抽取结果直接冻结并拆 kit，无人裁定。"""
    target = kbp.kit.freeze.freeze_auto(result, map_version)
    return target, kbp.kit.split.split(target)
