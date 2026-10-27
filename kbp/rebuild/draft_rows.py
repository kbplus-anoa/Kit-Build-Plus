"""草稿与提交的行格式：命题用 JSON 存，键名 head/connection/tail。

存取两侧共用这里，避免两处各写一遍字段顺序。
"""

import json

import kbp.contracts.submission


def pack(props) -> str:
    return json.dumps([{"head": p.head_id, "connection": p.connection,
                        "tail": p.tail_id} for p in props],
                      ensure_ascii=False)


def prop(raw: dict) -> kbp.contracts.submission.SubmittedProposition:
    return kbp.contracts.submission.SubmittedProposition(
        head_id=raw["head"], connection=raw["connection"], tail_id=raw["tail"])


def draft_row(draft: kbp.contracts.submission.Draft) -> tuple:
    return (draft.participant_id, draft.material_id, draft.time_point,
            draft.submit_seq, draft.map_version, draft.fingerprint, draft.mode,
            pack(draft.propositions), draft.saved_at)


def sub_row(sub: kbp.contracts.submission.Submission) -> tuple:
    return (sub.participant_id, sub.material_id, sub.time_point, sub.submit_seq,
            sub.map_version, sub.fingerprint, sub.mode, pack(sub.propositions),
            sub.started_at, sub.submitted_at)


def draft_from_row(participant_id: int, row) -> kbp.contracts.submission.Draft:
    return kbp.contracts.submission.Draft(
        map_version=row[3], fingerprint=row[4], mode=row[5],
        propositions=tuple(prop(p) for p in json.loads(row[6])),
        participant_id=participant_id, material_id=row[0], time_point=row[1],
        submit_seq=row[2], saved_at=row[7])


def sub_from_row(participant_id: int,
                 row) -> kbp.contracts.submission.Submission:
    return kbp.contracts.submission.Submission(
        map_version=row[3], fingerprint=row[4], mode=row[5],
        propositions=tuple(prop(p) for p in json.loads(row[6])),
        started_at=row[7], submitted_at=row[8], participant_id=participant_id,
        material_id=row[0], time_point=row[1], submit_seq=row[2])
