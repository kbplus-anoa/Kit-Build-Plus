"""测验作答与计分两块的请求/响应模型。"""

from pydantic import BaseModel, Field


class AnswerIn(BaseModel):
    question_id: str = Field(min_length=1, max_length=50)
    choice_index: int = Field(ge=-1, le=7)


class QuestionIn(BaseModel):
    question_id: str = Field(min_length=1, max_length=50)
    stem: str = Field(min_length=1, max_length=2000)
    choices: list[str] = Field(min_length=2, max_length=8)
    answer_index: int = Field(ge=0, le=7)
    qtype: str
    content_dimension: str = Field(default="", max_length=200)


class QuizIn(BaseModel):
    quiz_id: str = Field(min_length=1, max_length=100)
    target_map_version: str = Field(default="", max_length=50)  # 本次作答对应的图版本
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    time_point: str
    questions: list[QuestionIn] = Field(min_length=1, max_length=500)
    answers: list[AnswerIn] = Field(max_length=500)


class QuizOut(BaseModel):
    quiz_id: str
    time_point: str
    percent: float
    answered: int
