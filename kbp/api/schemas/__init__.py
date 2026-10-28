"""路由层的请求/响应模型。只做格式转换，不含业务规则。

按域拆开存放，名字仍从 kbp.api.schemas 统一导出。
"""

from kbp.api.schemas.core import (AdjudicationIn, BatchIn, BatchOut, ConfigIn,
                                  ConfigOut, ExtractIn, ExtractOut, IngestIn,
                                  IngestOut, MAX_TEXT, MaterialOut,
                                  MaterialsOut, MaterialTextOut, TripleOut,
                                  UploadOut, VocabIn)
from kbp.api.schemas.flow import (CurrentDraftIn, DraftIn, DraftOut, DraftsOut,
                                  ErrorOut, RecordOut, RecordsOut, ScoreOut,
                                  SubmitIn, SubmitOut, Vec2In)
from kbp.api.schemas.kit import (BuildKitIn, ConceptOut, JobOut, KitAutoIn,
                                 KitAutoOut, KitOut, PreviewIn, PreviewOut,
                                 ReadyOut, SignalOut)
from kbp.api.schemas.quiz import AnswerIn, QuestionIn, QuizIn, QuizOut

__all__ = [
    "AdjudicationIn", "AnswerIn", "BatchIn", "BatchOut", "BuildKitIn",
    "ConceptOut", "ConfigIn", "ConfigOut", "CurrentDraftIn", "DraftIn",
    "DraftOut", "DraftsOut", "ErrorOut", "ExtractIn", "ExtractOut",
    "IngestIn", "IngestOut", "JobOut", "KitAutoIn", "KitAutoOut", "KitOut",
    "MAX_TEXT", "MaterialOut", "MaterialTextOut", "MaterialsOut",
    "PreviewIn", "PreviewOut", "QuestionIn", "QuizIn", "QuizOut",
    "ReadyOut", "RecordOut", "RecordsOut", "ScoreOut", "SignalOut",
    "SubmitIn", "SubmitOut", "TripleOut", "UploadOut", "Vec2In", "VocabIn",
]
