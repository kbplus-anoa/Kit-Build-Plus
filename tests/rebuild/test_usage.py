import kbp.rebuild.draft_store as ds
import kbp.contracts.submission as submission
import kbp.rebuild.usage as usage


def final(map_version="v1", tp=submission.POST, seq=1, fingerprint="fp1"):
    return submission.Submission(map_version=map_version, fingerprint=fingerprint,
                                 mode=submission.TEST, propositions=(),
                                 started_at="", submitted_at="2026-10-25T10:00:00",
                                 participant_id=1, material_id=1, time_point=tp,
                                 submit_seq=seq)


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
    ds.submit(conn, final("v1", seq=1))
    ds.submit(conn, final("v2", seq=2))
    assert usage.lock_versions(conn) == ("v1", "v2")
    conn.close()


def test_指纹用过即锁定():
    conn = ds.connect(":memory:")
    assert usage.fingerprint_used(conn, "fp1") is False
    ds.submit(conn, final(fingerprint="fp1"))
    assert usage.fingerprint_used(conn, "fp1") is True
    assert usage.fingerprint_used(conn, "fp2") is False
    conn.close()


def test_空指纹视为已用():
    """空指纹分不清是哪份图，一律当已用，避免误改。"""
    conn = ds.connect(":memory:")
    assert usage.fingerprint_used(conn, "") is True
    conn.close()
