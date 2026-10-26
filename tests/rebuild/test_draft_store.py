import pytest

import kbp.rebuild.draft_store as ds
import kbp.contracts.submission as submission


def prop(head, conn, tail):
    return submission.SubmittedProposition(
        head_id=head, connection=conn, tail_id=tail)


def default_props():
    return (prop("c1", "包括", "c2"),)


def draft(session=1, props=None):
    return submission.Draft(map_version="v1", mode=submission.STUDY,
                            propositions=tuple(props or default_props()),
                            participant_id=1, material_id=1, session=session,
                            saved_at="2026-10-25T10:00:00")


def final(session=1, props=None):
    return submission.Submission(map_version="v1", mode=submission.TEST,
                                 propositions=tuple(props or default_props()),
                                 started_at="2026-10-25T09:00:00",
                                 submitted_at="2026-10-25T10:00:00",
                                 participant_id=1, material_id=1,
                                 session=session)


@pytest.fixture
def conn():
    c = ds.connect(":memory:")
    yield c
    c.close()


def test_保存并读回草稿(conn):
    ds.save(conn, draft())
    got = ds.load(conn, 1, 1, 1)
    assert got.mode == submission.STUDY
    assert got.propositions[0].connection == "包括"


def test_同场次草稿可被覆盖(conn):
    ds.save(conn, draft(props=(prop("c1", "属于", "c2"),)))
    ds.save(conn, draft(props=(prop("c1", "包括", "c2"),)))
    assert ds.load(conn, 1, 1, 1).propositions[0].connection == "包括"


def test_不同场次互不覆盖(conn):
    ds.save(conn, draft(session=1))
    ds.save(conn, draft(session=2))
    assert ds.load(conn, 1, 1, 2).session == 2


def test_读不存在草稿报错(conn):
    with pytest.raises(ds.DraftError):
        ds.load(conn, 9, 9, 9)


def test_提交后删除草稿(conn):
    ds.save(conn, draft())
    ds.submit(conn, final())
    with pytest.raises(ds.DraftError):
        ds.load(conn, 1, 1, 1)


def test_提交后不可再存草稿(conn):
    ds.save(conn, draft())
    ds.submit(conn, final())
    with pytest.raises(ds.DraftError):
        ds.save(conn, draft())


def test_同场次不可重复提交(conn):
    ds.submit(conn, final())
    with pytest.raises(ds.DraftError):
        ds.submit(conn, final())


def test_主动丢弃草稿(conn):
    ds.save(conn, draft())
    ds.drop(conn, 1, 1, 1)
    with pytest.raises(ds.DraftError):
        ds.load(conn, 1, 1, 1)


def test_落盘后重开可读回(tmp_path):
    path = str(tmp_path / "sub" / "kb.sqlite3")
    c1 = ds.connect(path)
    ds.save(c1, draft())
    c1.close()
    c2 = ds.connect(path)
    assert ds.load(c2, 1, 1, 1).map_version == "v1"
    c2.close()
