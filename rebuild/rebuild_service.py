import draft_store
import rebuild_validate as validate
import submission


class RebuildError(RuntimeError):
    """重建流程错误。"""


def save_draft(conn, kit, draft: submission.Draft) -> None:
    """保存草稿前先按 kit 校验，越界零件不得入库。"""
    _check(kit, draft.mode, draft.propositions,
           draft.participant_id, draft.material_id, draft.session)
    draft_store.save(conn, draft)


def submit(conn, kit, sub: submission.Submission) -> None:
    """提交：再校验一次，然后落库并删除草稿。"""
    _check(kit, sub.mode, sub.propositions,
           sub.participant_id, sub.material_id, sub.session)
    draft_store.submit(conn, sub)


def _check(kit, mode, props, participant_id, material_id, session) -> None:
    validate.check_mode(mode)
    validate.check_keys(participant_id, material_id, session)
    validate.check_against_kit(kit, props)
