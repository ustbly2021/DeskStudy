"""
数据模型初始化
"""

from app.DeskStudy.models.question import Question
from app.DeskStudy.models.review_record import ReviewRecord
from app.DeskStudy.models.wrong_question import WrongQuestion
from app.DeskStudy.models.user_config import UserConfig
from app.DeskStudy.models.study_statistics import StudyStatistics

__all__ = [
    "Question",
    "ReviewRecord",
    "WrongQuestion",
    "UserConfig",
    "StudyStatistics"
]
