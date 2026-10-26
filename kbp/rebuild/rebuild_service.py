import kbp.rebuild.draft_store
import kbp.rebuild.rebuild_validate
import kbp.contracts.submission


class RebuildError(RuntimeError):
    """重建流程错误。"""


def save_draft(conn, kit, draft: kbp.contracts.submission.Draft) -> None:
    """保存草稿前先按 kit 校验，越界零件不得入库。"""
    _check(kit, draft.mode, draft.propositions,
           draft.participant_id, draft.material_id, draft.session)
    kbp.rebuild.draft_store.save(conn, draft)


def submit(conn, kit, sub: kbp.contracts.submission.Submission) -> None:
    """提交：再校验一次，然后落库并删除草稿。"""
    _check(kit, sub.mode, sub.propositions,
           sub.participant_id, sub.material_id, sub.session)
    kbp.rebuild.draft_store.submit(conn, sub)


def _check(kit, mode, props, participant_id, material_id, session) -> None:
    kbp.rebuild.rebuild_validate.check_mode(mode)
    kbp.rebuild.rebuild_validate.check_keys(participant_id, material_id, session)
    kbp.rebuild.rebuild_validate.check_against_kit(kit, props)
