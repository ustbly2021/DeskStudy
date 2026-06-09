"""
错题本服务
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.DeskStudy.database.connection import get_database
from app.DeskStudy.models.wrong_question import WrongQuestion
from app.DeskStudy.models.question import Question
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class WrongQuestionService:
    """错题本服务"""

    def __init__(self):
        self.db = get_database()

    def get_session(self) -> Session:
        return self.db.get_session()

    def add_wrong_question(
        self,
        question_id: int,
        wrong_answer: str
    ) -> WrongQuestion:
        """添加错题记录"""
        session = self.get_session()
        try:
            existing = session.query(WrongQuestion).filter(
                WrongQuestion.question_id == question_id
            ).first()

            if existing:
                existing.wrong_count += 1
                existing.last_wrong_time = datetime.now()
                existing.wrong_answer = wrong_answer
                existing.mastery_level = max(0, existing.mastery_level - 10)
                session.commit()
                session.refresh(existing)
                logger.info(f"更新错题: question_id={question_id}, 错误次数={existing.wrong_count}")
                return existing
            else:
                wrong_q = WrongQuestion(
                    question_id=question_id,
                    wrong_answer=wrong_answer,
                    wrong_count=1,
                    mastery_level=50
                )
                session.add(wrong_q)
                session.commit()
                session.refresh(wrong_q)
                logger.info(f"新增错题: question_id={question_id}")
                return wrong_q
        except Exception as e:
            session.rollback()
            logger.error(f"添加错题失败: {e}")
            raise
        finally:
            session.close()

    def get_wrong_question(self, question_id: int) -> Optional[WrongQuestion]:
        """获取错题记录"""
        session = self.get_session()
        try:
            return session.query(WrongQuestion).filter(
                WrongQuestion.question_id == question_id
            ).first()
        finally:
            session.close()

    def get_all_wrong_questions(self) -> List[WrongQuestion]:
        """获取所有错题"""
        session = self.get_session()
        try:
            return session.query(WrongQuestion).order_by(
                WrongQuestion.last_wrong_time.desc()
            ).all()
        finally:
            session.close()

    def get_wrong_questions_for_review(self, limit: int = 10) -> List[WrongQuestion]:
        """获取需要复习的错题（按错误次数和掌握程度排序）"""
        session = self.get_session()
        try:
            return session.query(WrongQuestion).order_by(
                WrongQuestion.mastery_level.asc(),
                WrongQuestion.wrong_count.desc(),
                WrongQuestion.last_wrong_time.asc()
            ).limit(limit).all()
        finally:
            session.close()

    def update_mastery_level(self, question_id: int, correct: bool) -> None:
        """更新掌握程度"""
        session = self.get_session()
        try:
            wrong_q = session.query(WrongQuestion).filter(
                WrongQuestion.question_id == question_id
            ).first()

            if wrong_q:
                if correct:
                    wrong_q.mastery_level = min(100, wrong_q.mastery_level + 15)
                else:
                    wrong_q.mastery_level = max(0, wrong_q.mastery_level - 10)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"更新掌握程度失败: {e}")
            raise
        finally:
            session.close()

    def remove_wrong_question(self, question_id: int) -> bool:
        """移除错题（已掌握）"""
        session = self.get_session()
        try:
            wrong_q = session.query(WrongQuestion).filter(
                WrongQuestion.question_id == question_id
            ).first()

            if wrong_q:
                session.delete(wrong_q)
                session.commit()
                logger.info(f"移除错题: question_id={question_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"移除错题失败: {e}")
            raise
        finally:
            session.close()

    def clear_all_wrong_questions(self) -> int:
        """清空所有错题"""
        session = self.get_session()
        try:
            count = session.query(WrongQuestion).delete()
            session.commit()
            logger.info(f"清空错题本: {count}条")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"清空错题本失败: {e}")
            raise
        finally:
            session.close()

    def get_wrong_count(self) -> int:
        """获取错题数量"""
        session = self.get_session()
        try:
            return session.query(WrongQuestion).count()
        finally:
            session.close()

    def get_wrong_question_with_details(self, wrong_id: int) -> Optional[Dict[str, Any]]:
        """获取错题详情（包含题目内容）"""
        session = self.get_session()
        try:
            wrong_q = session.query(WrongQuestion).filter(
                WrongQuestion.id == wrong_id
            ).first()

            if wrong_q:
                question = session.query(Question).filter(
                    Question.id == wrong_q.question_id
                ).first()

                if question:
                    return {
                        "wrong": wrong_q.to_dict(),
                        "question": question.to_dict()
                    }
            return None
        finally:
            session.close()

    def get_statistics(self) -> Dict[str, Any]:
        """获取错题统计"""
        session = self.get_session()
        try:
            total = session.query(WrongQuestion).count()
            recent = session.query(WrongQuestion).filter(
                WrongQuestion.last_wrong_time >= datetime.now() - timedelta(days=7)
            ).count()

            mastered = session.query(WrongQuestion).filter(
                WrongQuestion.mastery_level >= 80
            ).count()

            return {
                "total": total,
                "recent_week": recent,
                "mastered": mastered,
                "need_review": total - mastered
            }
        finally:
            session.close()
