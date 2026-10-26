import kbp.contracts.quizsheet
import kbp.contracts.submission


class QuizError(ValueError):
    """题目或作答不合法。"""


def check_question(q: kbp.contracts.quizsheet.Question) -> None:
    """单选必须恰好一个正确答案，选项数在范围内。"""
    if not q.question_id.strip():
        raise QuizError("题号不得为空")
    if len(q.stem) > kbp.contracts.quizsheet.MAX_STEM:
        raise QuizError("题干超长: " + q.question_id)
    if len(q.choices) < 2:
        raise QuizError("选项少于两个: " + q.question_id)
    if len(q.choices) > kbp.contracts.quizsheet.MAX_CHOICES:
        raise QuizError("选项过多: " + q.question_id)
    if not 0 <= q.answer_index < len(q.choices):
        raise QuizError("正确答案下标越界: " + q.question_id)
    if q.qtype not in kbp.contracts.quizsheet.QUESTION_TYPES:
        raise QuizError("未知题型: " + str(q.qtype))


def is_correct(q: kbp.contracts.quizsheet.Question, answer: kbp.contracts.quizsheet.Answer) -> bool:
    """答对判定：未作答（-1）一律算错。"""
    if answer.choice_index < 0:
        return False
    return answer.choice_index == q.answer_index


def percent(questions, record: kbp.contracts.quizsheet.QuizRecord) -> float:
    """百分制 0–100，分母为题数；题数为 0 取 0.0。"""
    if not questions:
        return 0.0
    answered = {a.question_id: a for a in record.answers}
    right = sum(1 for q in questions
                if q.question_id in answered
                and is_correct(q, answered[q.question_id]))
    return round(right / len(questions) * 100, 4)


def check_answer(answer: kbp.contracts.quizsheet.Answer, questions) -> None:
    """作答不得引用不存在的题，时点须合法。"""
    ids = {q.question_id for q in questions}
    if answer.question_id not in ids:
        raise QuizError("作答引用不存在的题: " + answer.question_id)
    if answer.time_point not in kbp.contracts.submission.TIME_POINTS:
        raise QuizError("未知时点: " + str(answer.time_point))


def check_record(record: kbp.contracts.quizsheet.QuizRecord, questions) -> None:
    """整卷校验：关联键、时点、题号、重复作答。"""
    _check_keys(record)
    if record.time_point not in kbp.contracts.submission.TIME_POINTS:
        raise QuizError("未知时点: " + str(record.time_point))
    seen: set[str] = set()
    for answer in record.answers:
        check_answer(answer, questions)
        if answer.time_point != record.time_point:
            raise QuizError("作答时点与整卷不一致: " + answer.question_id)
        if answer.question_id in seen:
            raise QuizError("同题重复作答: " + answer.question_id)
        seen.add(answer.question_id)


def _check_keys(record: kbp.contracts.quizsheet.QuizRecord) -> None:
    reason = kbp.contracts.submission.check_key(
        record.participant_id, record.material_id, record.time_point,
        record.submit_seq)
    if reason:
        raise QuizError(reason)
