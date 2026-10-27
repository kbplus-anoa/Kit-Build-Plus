import kbp.rebuild.draft_store
import kbp.rebuild.rebuild_validate
import kbp.contracts.submission


class RebuildError(RuntimeError):
    """重建流程错误。"""


def save_draft(conn, kit, draft: kbp.contracts.submission.Draft) -> None:
    """保存草稿前先按 kit 校验，越界零件不得入库。"""
    _check(kit, draft)
    kbp.rebuild.draft_store.save(conn, draft)


def load_draft(conn, participant_id: int, material_id: int, time_point: str,
               submit_seq: int) -> kbp.contracts.submission.Draft:
    """读回草稿；不存在时报错。"""
    return kbp.rebuild.draft_store.load(conn, participant_id, material_id,
                                        time_point, submit_seq)


def submit(conn, kit, sub: kbp.contracts.submission.Submission) -> None:
    """提交：再校验一次，然后落库并删除草稿。"""
    _check(kit, sub)
    kbp.rebuild.draft_store.submit(conn, sub)


def _check(kit, obj) -> None:
    kbp.rebuild.rebuild_validate.check_mode(obj.mode)
    kbp.rebuild.rebuild_validate.check_keys(
        obj.participant_id, obj.material_id, obj.time_point, obj.submit_seq)
    kbp.rebuild.rebuild_validate.check_against_kit(kit, obj.propositions)
