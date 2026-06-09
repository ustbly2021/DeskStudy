"""
题目模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import relationship

from app.DeskStudy.database.connection import Base


class Question(Base):
    """题目表"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False, comment="题目内容")
    option_a = Column(Text, nullable=False, comment="选项A")
    option_b = Column(Text, nullable=False, comment="选项B")
    option_c = Column(Text, nullable=True, comment="选项C")
    option_d = Column(Text, nullable=True, comment="选项D")
    correct_answer = Column(String(10), nullable=False, comment="正确答案")
    explanation = Column(Text, nullable=True, comment="解析")
    category = Column(String(100), nullable=True, comment="分类")
    correct_rate = Column(Float, default=0.0, comment="全站正确率(%)")
    source = Column(String(200), nullable=True, comment="来源")
    question_type = Column(String(20), default="single", comment="题型: single/multiple/judgment")
    is_judgment = Column(Boolean, default=False, comment="是否为判断题")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    review_records = relationship("ReviewRecord", back_populates="question", cascade="all, delete-orphan")
    wrong_questions = relationship("WrongQuestion", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, content={self.content[:20]}...)>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "option_c": self.option_c,
            "option_d": self.option_d,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "category": self.category,
            "correct_rate": self.correct_rate,
            "source": self.source,
            "question_type": self.question_type,
            "is_judgment": self.is_judgment,
            "create_time": self.create_time.isoformat() if self.create_time else None
        }
