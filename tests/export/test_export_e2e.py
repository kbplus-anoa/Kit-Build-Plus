"""端到端：建图提交 → 判分 → 被试级 CSV 落盘。

装配层职责：本用例自己把 score / export 串起来，feature 之间仍互不 import。
"""


import kbp.contracts.exportcsv as exportcsv  # noqa: E402
import kbp.export.csv_writer as csv_writer  # noqa: E402
import kbp.export.subject_table as subject_table  # noqa: E402
import kbp.score.score_service as score_service  # noqa: E402
import kbp.contracts.submission as submission  # noqa: E402
import kbp.contracts.targetmap as targetmap  # noqa: E402
import kbp.contracts.triple as triple  # noqa: E402


def test_提交到被试级_CSV(tmp_path):
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括",))
    target = targetmap.TargetMap(
        map_version="v1", vocab=v,
        concepts=(targetmap.Concept(concept_id="c1", label="记忆"),
                  targetmap.Concept(concept_id="c2", label="短时记忆")),
        propositions=(targetmap.Proposition(head_id="c1", connection="包括",
                                            tail_id="c2"),))
    sub = submission.Submission(
        map_version="v1", fingerprint=target.fingerprint,
        mode=submission.TEST,
        propositions=(submission.SubmittedProposition(
            head_id="c1", connection="包括", tail_id="c2"),),
        started_at="", submitted_at="2026-10-25T10:00:00",
        participant_id=1, material_id=1, time_point=submission.POST,
        submit_seq=1)
    scored = score_service.score(target, sub)
    counts = score_service.summary(scored)

    s_row = exportcsv.SubjectRow(
        participant_id=1, material_id=1, time_point="post", submit_seq=1,
        target_map_version="v1", fingerprint=target.fingerprint,
        mode="test", condition="exp", is_practice=0,
        correct_propositions=scored.correct_propositions,
        total_propositions=scored.total_propositions,
        n_lacking=counts["lacking"], n_excessive=counts["excessive"],
        n_leaving=counts["leaving"], n_reversed=counts["reversed"],
        possibly_inaccurate=0, map_size=1, map_node_count=2,
        signal_isolated=0.0, signal_coverage=1.0,
        signal_concentration=1.0, signal_baseline=0.0)

    out = tmp_path / "subject.csv"
    out.write_bytes(csv_writer.to_csv(subject_table.build((s_row,))))

    assert out.read_bytes().startswith(b"\xef\xbb\xbf")
    text = out.read_bytes().decode("utf-8-sig")
    assert "participant_id" in text
    assert "1.00000000" in text
    assert len(text.strip().splitlines()) == 2
