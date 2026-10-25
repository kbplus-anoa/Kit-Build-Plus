import draft_store as ds
import submission
import usage


def final(map_version="v1", session=1):
    return submission.Submission(map_version=map_version,
                                 mode=submission.TEST, propositions=(),
                                 started_at="", submitted_at="2026-10-25T10:00:00",
                                 participant_id=1, material_id=1,
                                 session=session)


def test_未提交时版本未锁定():
    conn = ds.connect(":memory:")
    assert usage.SubmissionUsage(conn).is_used("v1") is False
    conn.close()


def test_提交后该版本锁定():
    conn = ds.connect(":memory:")
    ds.submit(conn, final("v1"))
    assert usage.SubmissionUsage(conn).is_used("v1") is True
    conn.close()


def test_其他版本不受影响():
    conn = ds.connect(":memory:")
    ds.submit(conn, final("v1"))
    assert usage.SubmissionUsage(conn).is_used("v2") is False
    conn.close()


def test_空版本视为已锁定():
    conn = ds.connect(":memory:")
    assert usage.SubmissionUsage(conn).is_used("") is True
    conn.close()


def test_列出被用过的版本():
    conn = ds.connect(":memory:")
    ds.submit(conn, final("v1", session=1))
    ds.submit(conn, final("v2", session=2))
    assert usage.lock_versions(conn) == ("v1", "v2")
    conn.close()
