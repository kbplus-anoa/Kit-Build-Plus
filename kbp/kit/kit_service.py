import kbp.contracts.adjudication
import kbp.contracts.extraction
import kbp.contracts.targetbank
import kbp.kit._rules
import kbp.kit.adopt
import kbp.kit.bank_store
import kbp.kit.dev_overlay
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


def freeze_and_bank(conn, material_id: int, batch_id: str,
                    map_version: str):
    """人工裁定路：冻结后登记题库，返回（图, kit）。

    教材标识不在裁定记录里，只能由调用方给；同一张图已在库就回旧图，
    不新开行，也不改旧图的版本号。
    """
    target = freeze_batch(conn, batch_id, map_version)
    entry = kbp.kit.bank_store.by_fingerprint(conn, material_id,
                                              target.fingerprint)
    if entry is None:
        entry = kbp.kit.adopt.entry(material_id, batch_id, target,
                                    kbp.kit.adopt.now())
        kbp.kit.bank_store.register(conn, entry)
    return entry.target_map, kbp.kit.split.split(entry.target_map)


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


def bank_kit(conn, entry):
    """命中题库后直接拿到学生零件集，不再重抽；开发期改写一并盖上。"""
    return target_kit(conn, entry)


def history(conn, material_id: int, vocab_version: str = ""):
    """该教材已冻结的各批，按入库先后；新抽的排在旧批之后，旧批不动。"""
    return kbp.kit.bank_store.history(conn, material_id, vocab_version)


def _version_entry(conn, material_id: int, map_version: str):
    """按版本号取题库里那一批；不存在抛 BankError。"""
    entry = kbp.kit.bank_store.by_version(conn, material_id, map_version)
    if entry is None:
        raise kbp.kit.bank_store.BankError("版本不存在: " + map_version)
    return entry


def version_kit(conn, material_id: int, map_version: str):
    """按版本号取那一批的零件集；切回旧批或预览某一批都用它。"""
    return target_kit(conn, _version_entry(conn, material_id, map_version))


def target_kit(conn, entry):
    """题库里那一批的图与零件集：开发者改写盖在冻结图上，指纹与版本号不动。

    改过的那一批按库里存的零件给 kit，不再从命题反推：开发者可以先加
    概念、后加用到它的命题，中间那一步读图也得看得见这个零件。
    """
    overlay = kbp.kit.dev_overlay.load(conn, entry.material_id,
                                       entry.target_map.map_version)
    target = kbp.kit.dev_overlay.apply(entry.target_map, overlay)
    if overlay is None:
        return target, kbp.kit.split.split(target)
    kit = kbp.contracts.targetmap.Kit(map_version=target.map_version,
                                      concepts=overlay.concepts,
                                      connections=overlay.connections)
    return target, kit


def use(conn, material_id: int, map_version: str):
    """把某一版本标为已投用；学生切回旧批也走这里，版本不存在抛 BankError。"""
    _version_entry(conn, material_id, map_version)
    kbp.kit.bank_store.mark_in_use(conn, material_id, map_version)
    return kbp.kit.bank_store.by_version(conn, material_id, map_version)


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
