import draft_store as ds
import rebuild_service as svc
import submission
import targetmap


def concept(cid, label):
    return targetmap.Concept(concept_id=cid, label=label)


def make_kit():
    return targetmap.Kit(map_version="v1",
                         concepts=(concept("c1", "记忆"), concept("c2", "短时记忆")),
                         connections=("包括",))


def prop(head, conn, tail):
    return submission.SubmittedProposition(
        head_id=head, connection=conn, tail_id=tail)


def draft(props=None):
    return submission.Draft(map_version="v1", mode=submission.STUDY,
                            propositions=tuple(props or (prop("c1", "包括", "c2"),)),
                            participant_id=1, material_id=1, session=1,
                            saved_at="2026-10-25T10:00:00")


def final(props=None):
    return submission.Submission(map_version="v1", mode=submission.TEST,
                                 propositions=tuple(props or (prop("c1", "包括", "c2"),)),
                                 started_at="", submitted_at="2026-10-25T10:00:00",
                                 participant_id=1, material_id=1, session=1)


def test_合法草稿入库():
    conn = ds.connect(":memory:")
    svc.save_draft(conn, make_kit(), draft())
    assert ds.load(conn, 1, 1, 1).propositions[0].connection == "包括"
    conn.close()


def test_越界零件草稿被拒且不入库():
    conn = ds.connect(":memory:")
    try:
        svc.save_draft(conn, make_kit(), draft((prop("c9", "包括", "c2"),)))
    except Exception:
        pass
    try:
        ds.load(conn, 1, 1, 1)
        leaked = True
    except ds.DraftError:
        leaked = False
    assert leaked is False
    conn.close()


def test_提交后草稿清空():
    conn = ds.connect(":memory:")
    svc.save_draft(conn, make_kit(), draft())
    svc.submit(conn, make_kit(), final())
    try:
        ds.load(conn, 1, 1, 1)
        gone = False
    except ds.DraftError:
        gone = True
    assert gone is True
    conn.close()


def test_非法模式提交被拒():
    conn = ds.connect(":memory:")
    bad = submission.Submission(map_version="v1", mode="exam", propositions=(),
                                started_at="", submitted_at="",
                                participant_id=1, material_id=1, session=1)
    try:
        svc.submit(conn, make_kit(), bad)
        raised = False
    except Exception:
        raised = True
    assert raised is True
    conn.close()
