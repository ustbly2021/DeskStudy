"""
学习统计数据模型
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Date, Float

from app.DeskStudy.database.connection import Base


class StudyStatistics(Base):
    """学习统计表"""
    __tablename__ = "study_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, unique=True, nullable=False, comment="统计日期")
    questions_answered = Column(Integer, default=0, comment="答题数")
    correct_count = Column(Integer, default=0, comment="正确数")
    wrong_count = Column(Integer, default=0, comment="错误数")
    study_duration = Column(Integer, default=0, comment="学习时长(秒)")
    review_count = Column(Integer, default=0, comment="复习题数")
    new_count = Column(Integer, default=0, comment="新题数")
    accuracy_rate = Column(Float, default=0.0, comment="正确率")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"<StudyStatistics(date={self.stat_date}, answered={self.questions_answered})>"

    def calculate_accuracy(self) -> float:
        """计算正确率"""
        if self.questions_answered == 0:
            return 0.0
        return round(self.correct_count / self.questions_answered * 100, 2)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "stat_date": self.stat_date.isoformat() if self.stat_date else None,
            "questions_answered": self.questions_answered,
            "correct_count": self.correct_count,
            "wrong_count": self.wrong_count,
            "study_duration": self.study_duration,
            "review_count": self.review_count,
            "new_count": self.new_count,
            "accuracy_rate": self.accuracy_rate
        }
