import kbp.contracts.adjudication as adjudication
import kbp.kit.kit_service as kit_service
import kbp.kit.store as store
import kbp.contracts.triple as triple


def cand(head, conn, tail):
    return triple.TripleCandidate(head=head, connection=conn, tail=tail,
                                  confidence=0.9)


def with_items(items):
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括", "属于", "导致"))
    return adjudication.AdjudicationLog(batch_id="b1", vocab=v, items=tuple(items))


def acc(head, c, tail):
    return adjudication.Adjudication(candidate=cand(head, c, tail),
                                     decision=adjudication.ACCEPTED, reason="")


def rej(head, c, tail):
    return adjudication.Adjudication(candidate=cand(head, c, tail),
                                     decision=adjudication.REJECTED,
                                     reason="教材未提及")


def test_落库到拆_kit_全流程(tmp_path):
    conn = store.connect(str(tmp_path / "kb.sqlite3"))
    log = with_items([acc("记忆", "包括", "短时记忆"), rej("长度", "包括", "容量")])
    kit_service.adjudicate(conn, log)
    kit = kit_service.build_kit(conn, "b1", "v1")
    assert [c.label for c in kit.concepts] == ["记忆", "短时记忆"]
    assert kit.connections == ("包括",)
    conn.close()


def test_驳回项不进_kit(tmp_path):
    conn = store.connect(":memory:")
    kit_service.adjudicate(conn, with_items([acc("记忆", "包括", "短时记忆"),
                                             rej("长度", "包括", "容量")]))
    kit = kit_service.build_kit(conn, "b1", "v1")
    assert "容量" not in [c.label for c in kit.concepts]
    conn.close()


def test_驳回项仍可读回留档(tmp_path):
    conn = store.connect(":memory:")
    kit_service.adjudicate(conn, with_items([acc("记忆", "包括", "短时记忆"),
                                             rej("长度", "包括", "容量")]))
    log = kit_service.load_batch(conn, "b1")
    assert len(log.items) == 2
    assert log.items[1].decision == adjudication.REJECTED
    conn.close()


def test_冻结结果带版本号(tmp_path):
    conn = store.connect(":memory:")
    kit_service.adjudicate(conn, with_items([acc("记忆", "包括", "短时记忆")]))
    assert kit_service.build_kit(conn, "b1", "v2").map_version == "v2"
    conn.close()
