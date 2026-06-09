"""
服务模块初始化
"""

from app.DeskStudy.services.question_service import QuestionService
from app.DeskStudy.services.wrong_question_service import WrongQuestionService
from app.DeskStudy.services.review_service import ReviewService
from app.DeskStudy.services.statistics_service import StatisticsService
from app.DeskStudy.services.config_service import ConfigService

__all__ = [
    "QuestionService",
    "WrongQuestionService",
    "ReviewService",
    "StatisticsService",
    "ConfigService"
]
