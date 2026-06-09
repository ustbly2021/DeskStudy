"""
复习记录模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.DeskStudy.database.connection import Base


class ReviewRecord(Base):
    """复习记录表 - 用于艾宾浩斯复习调度"""
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    review_date = Column(DateTime, default=datetime.now, comment="复习日期")
    next_review_date = Column(DateTime, nullable=True, comment="下次复习日期")
    interval_days = Column(Integer, default=1, comment="间隔天数")
    ease_factor = Column(Float, default=2.5, comment="难度系数")
    repetition_count = Column(Integer, default=0, comment="重复次数")
    last_result = Column(String(20), nullable=True, comment="上次结果: correct/wrong")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    question = relationship("Question", back_populates="review_records")

    def __repr__(self) -> str:
        return f"<ReviewRecord(id={self.id}, question_id={self.question_id}, next_review={self.next_review_date})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "review_date": self.review_date.isoformat() if self.review_date else None,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "interval_days": self.interval_days,
            "ease_factor": self.ease_factor,
            "repetition_count": self.repetition_count,
            "last_result": self.last_result
        }
