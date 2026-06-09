"""
错题本模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.DeskStudy.database.connection import Base


class WrongQuestion(Base):
    """错题表"""
    __tablename__ = "wrong_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    wrong_count = Column(Integer, default=1, comment="错误次数")
    last_wrong_time = Column(DateTime, default=datetime.now, comment="最近错误时间")
    mastery_level = Column(Integer, default=0, comment="掌握程度 0-100")
    wrong_answer = Column(String(10), nullable=True, comment="错误答案")
    notes = Column(Text, nullable=True, comment="笔记")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    question = relationship("Question", back_populates="wrong_questions")

    def __repr__(self) -> str:
        return f"<WrongQuestion(id={self.id}, question_id={self.question_id}, wrong_count={self.wrong_count})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "wrong_count": self.wrong_count,
            "last_wrong_time": self.last_wrong_time.isoformat() if self.last_wrong_time else None,
            "mastery_level": self.mastery_level,
            "wrong_answer": self.wrong_answer,
            "notes": self.notes
        }
