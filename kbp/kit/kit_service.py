import kbp.contracts.adjudication
import kbp.contracts.extraction
import kbp.contracts.targetbank
import kbp.kit._rules
import kbp.kit.bank_store
import kbp.kit.freeze
import kbp.kit.lock
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


def bank_find(conn, material_id: int, vocab_version: str):
    """题库命中：同教材同词表版本已冻结过一张图，就直接用，不重抽。"""
    return kbp.kit.bank_store.latest(conn, material_id, vocab_version)


def bank_kit(entry):
    """命中题库后直接拿到学生零件集，不再重抽。"""
    return entry.target_map, kbp.kit.split.split(entry.target_map)


def next_free_version(conn, material_id: int, want: str = "") -> str:
    """分配版本号：想要且未占用就用它，被占用了往后排，绝不覆盖旧图。"""
    used = kbp.kit.bank_store.versions(conn, material_id)
    if want and want not in used:
        return want
    return kbp.kit._rules.next_version(used)


def freeze_to_bank(conn, material_id: int,
                   result: kbp.contracts.triple.ExtractionResult,
                   created_at: str, want_version: str = "",
                   usage=None):
    """未命中题库时用：冻结 → 按指纹查重 → 登记，返回（图, kit, 登记项）。

    同一批内容再抽一次得到同一指纹，此时回已经库里的那张图，不新开版本。
    """
    version = next_free_version(conn, material_id, want_version)
    target = kbp.kit.freeze.freeze_auto(result, version)
    entry = kbp.kit.bank_store.by_fingerprint(conn, material_id, target.fingerprint)
    if entry is None:
        entry = _entry(material_id, target, created_at, usage)
        kbp.kit.bank_store.register(conn, entry)
    return entry.target_map, kbp.kit.split.split(entry.target_map), entry


def _entry(material_id: int, target, created_at: str, usage=None):
    if usage is not None:
        kbp.kit.lock.assert_mutable(target.map_version, usage)
    return kbp.contracts.targetbank.BankEntry(
        material_id=material_id, vocab_version=target.vocab.vocab_version,
        source=kbp.contracts.targetbank.AUTO, in_use=False,
        created_at=created_at, target_map=target)
