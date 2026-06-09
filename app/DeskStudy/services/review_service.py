"""
艾宾浩斯复习服务
实现基于艾宾浩斯遗忘曲线的复习调度算法
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.DeskStudy.database.connection import get_database
from app.DeskStudy.models.review_record import ReviewRecord
from app.DeskStudy.models.question import Question
from app.DeskStudy.models.wrong_question import WrongQuestion
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReviewNode:
    """复习节点定义"""
    day: int
    name: str


EBBINGHAUS_NODES = [
    ReviewNode(day=1, name="第1天"),
    ReviewNode(day=3, name="第3天"),
    ReviewNode(day=7, name="第7天"),
    ReviewNode(day=15, name="第15天"),
    ReviewNode(day=30, name="第30天"),
]


class ReviewService:
    """艾宾浩斯复习服务"""

    def __init__(self):
        self.db = get_database()

    def get_session(self) -> Session:
        return self.db.get_session()

    def create_review_record(self, question_id: int) -> ReviewRecord:
        """创建新的复习记录（新题首次学习）"""
        session = self.get_session()
        try:
            existing = session.query(ReviewRecord).filter(
                ReviewRecord.question_id == question_id
            ).first()

            if existing:
                return existing

            now = datetime.now()
            next_review = now + timedelta(days=1)

            record = ReviewRecord(
                question_id=question_id,
                review_date=now,
                next_review_date=next_review,
                interval_days=1,
                ease_factor=2.5,
                repetition_count=1
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(f"创建复习记录: question_id={question_id}")
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"创建复习记录失败: {e}")
            raise
        finally:
            session.close()

    def get_review_questions(self, limit: int = 10, exclude_ids: List[int] = None) -> List[Dict[str, Any]]:
        """
        获取需要复习的题目
        优先级：错题 > 待复习 > 新题 > 随机题目
        """
        session = self.get_session()
        try:
            from random import sample
            from sqlalchemy import and_, or_, not_

            now = datetime.now()
            exclude_ids = exclude_ids or []

            all_questions = session.query(Question).all()
            all_question_ids = [q.id for q in all_questions]

            available_ids = [qid for qid in all_question_ids if qid not in exclude_ids]

            if not available_ids:
                available_ids = all_question_ids

            wrong_question_ids = session.query(WrongQuestion.question_id).all()
            wrong_ids = [wq.question_id for wq in wrong_question_ids if wq.question_id in available_ids]

            due_records = session.query(ReviewRecord).filter(
                ReviewRecord.next_review_date <= now
            ).all()
            due_ids = [r.question_id for r in due_records if r.question_id in available_ids]

            reviewed_ids = [r.question_id for r in session.query(ReviewRecord.question_id).all()]
            new_ids = [qid for qid in available_ids if qid not in reviewed_ids]

            priority_ids = []

            for wid in wrong_ids[:limit]:
                if wid not in priority_ids:
                    priority_ids.append(wid)

            remaining = limit - len(priority_ids)

            if remaining > 0:
                for did in due_ids:
                    if did not in priority_ids:
                        priority_ids.append(did)
                        remaining -= 1
                        if remaining <= 0:
                            break

            if remaining > 0:
                for nid in new_ids:
                    if nid not in priority_ids:
                        priority_ids.append(nid)
                        remaining -= 1
                        if remaining <= 0:
                            break

            if remaining > 0:
                random_pool = [qid for qid in available_ids if qid not in priority_ids]
                if random_pool:
                    random_ids = sample(random_pool, min(remaining, len(random_pool)))
                    priority_ids.extend(random_ids)

            if not priority_ids:
                priority_ids = sample(available_ids, min(limit, len(available_ids))) if available_ids else []

            questions = session.query(Question).filter(
                Question.id.in_(priority_ids)
            ).all()

            result = []
            for q in questions:
                record = session.query(ReviewRecord).filter(
                    ReviewRecord.question_id == q.id
                ).first()
                result.append({
                    "question": q.to_dict(),
                    "review_record": record.to_dict() if record else None,
                    "is_wrong": q.id in wrong_ids
                })

            result.sort(key=lambda x: (
                0 if x["is_wrong"] else 1,
                x["review_record"]["next_review_date"] if x["review_record"] else ""
            ))

            return result[:limit]
        finally:
            session.close()

    def record_review_result(
        self,
        question_id: int,
        correct: bool
    ) -> ReviewRecord:
        """
        记录复习结果并计算下次复习时间
        使用艾宾浩斯算法调整间隔
        """
        session = self.get_session()
        try:
            record = session.query(ReviewRecord).filter(
                ReviewRecord.question_id == question_id
            ).first()

            now = datetime.now()

            if not record:
                record = self.create_review_record(question_id)
                session.refresh(record)

            record.repetition_count += 1
            record.last_result = "correct" if correct else "wrong"
            record.review_date = now

            if correct:
                if record.repetition_count == 1:
                    record.interval_days = 1
                elif record.repetition_count == 2:
                    record.interval_days = 3
                elif record.repetition_count == 3:
                    record.interval_days = 7
                else:
                    record.interval_days = int(record.interval_days * record.ease_factor)

                record.ease_factor = max(1.3, record.ease_factor + 0.1)
            else:
                record.repetition_count = 0
                record.interval_days = 1
                record.ease_factor = max(1.3, record.ease_factor - 0.2)

            record.next_review_date = now + timedelta(days=record.interval_days)

            session.commit()
            session.refresh(record)

            logger.info(
                f"复习结果: question_id={question_id}, "
                f"correct={correct}, next_review={record.next_review_date}"
            )

            return record
        except Exception as e:
            session.rollback()
            logger.error(f"记录复习结果失败: {e}")
            raise
        finally:
            session.close()

    def get_review_count(self) -> int:
        """获取待复习题目数量"""
        session = self.get_session()
        try:
            now = datetime.now()
            return session.query(ReviewRecord).filter(
                ReviewRecord.next_review_date <= now
            ).count()
        finally:
            session.close()

    def get_review_today_count(self) -> int:
        """获取今日已复习数量"""
        session = self.get_session()
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return session.query(ReviewRecord).filter(
                ReviewRecord.review_date >= today_start
            ).count()
        finally:
            session.close()

    def get_upcoming_reviews(self, days: int = 7) -> Dict[str, int]:
        """获取未来几天的复习计划"""
        session = self.get_session()
        try:
            now = datetime.now()
            result = {}

            for i in range(days):
                date = now + timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_start + timedelta(days=1)

                count = session.query(ReviewRecord).filter(
                    ReviewRecord.next_review_date >= date_start,
                    ReviewRecord.next_review_date < date_end
                ).count()

                result[date.strftime("%m-%d")] = count

            return result
        finally:
            session.close()

    def delete_review_record(self, question_id: int) -> bool:
        """删除复习记录"""
        session = self.get_session()
        try:
            record = session.query(ReviewRecord).filter(
                ReviewRecord.question_id == question_id
            ).first()

            if record:
                session.delete(record)
                session.commit()
                logger.info(f"删除复习记录: question_id={question_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除复习记录失败: {e}")
            raise
        finally:
            session.close()

    def reset_review_for_question(self, question_id: int) -> ReviewRecord:
        """重置题目的复习进度"""
        session = self.get_session()
        try:
            record = session.query(ReviewRecord).filter(
                ReviewRecord.question_id == question_id
            ).first()

            if record:
                session.delete(record)
                session.commit()

            return self.create_review_record(question_id)
        except Exception as e:
            session.rollback()
            logger.error(f"重置复习进度失败: {e}")
            raise
        finally:
            session.close()
