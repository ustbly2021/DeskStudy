"""
学习统计服务
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from app.DeskStudy.database.connection import get_database
from app.DeskStudy.models.study_statistics import StudyStatistics
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsService:
    """学习统计服务"""

    def __init__(self):
        self.db = get_database()

    def get_session(self) -> Session:
        return self.db.get_session()

    def _get_or_create_today_stat(self, session: Session) -> StudyStatistics:
        """获取或创建今日统计记录"""
        today = date.today()
        stat = session.query(StudyStatistics).filter(
            StudyStatistics.stat_date == today
        ).first()

        if not stat:
            stat = StudyStatistics(stat_date=today)
            session.add(stat)
            session.flush()

        return stat

    def record_answer(
        self,
        correct: bool,
        is_review: bool = False,
        is_new: bool = False
    ) -> None:
        """记录答题结果"""
        session = self.get_session()
        try:
            stat = self._get_or_create_today_stat(session)

            stat.questions_answered += 1

            if correct:
                stat.correct_count += 1
            else:
                stat.wrong_count += 1

            if is_review:
                stat.review_count += 1
            elif is_new:
                stat.new_count += 1

            stat.accuracy_rate = stat.calculate_accuracy()
            stat.update_time = datetime.now()

            session.commit()
            logger.debug(f"记录答题: correct={correct}")
        except Exception as e:
            session.rollback()
            logger.error(f"记录答题失败: {e}")
            raise
        finally:
            session.close()

    def record_study_duration(self, seconds: int) -> None:
        """记录学习时长"""
        session = self.get_session()
        try:
            stat = self._get_or_create_today_stat(session)
            stat.study_duration += seconds
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"记录学习时长失败: {e}")
            raise
        finally:
            session.close()

    def get_today_statistics(self) -> Dict[str, Any]:
        """获取今日统计"""
        session = self.get_session()
        try:
            stat = self._get_or_create_today_stat(session)
            return stat.to_dict()
        finally:
            session.close()

    def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """获取日期范围内的统计"""
        session = self.get_session()
        try:
            query = session.query(StudyStatistics)

            if start_date:
                query = query.filter(StudyStatistics.stat_date >= start_date)
            if end_date:
                query = query.filter(StudyStatistics.stat_date <= end_date)

            stats = query.order_by(StudyStatistics.stat_date.desc()).all()
            return [s.to_dict() for s in stats]
        finally:
            session.close()

    def get_total_statistics(self) -> Dict[str, Any]:
        """获取累计统计"""
        session = self.get_session()
        try:
            total = session.query(StudyStatistics).all()

            total_answered = sum(s.questions_answered for s in total)
            total_correct = sum(s.correct_count for s in total)
            total_duration = sum(s.study_duration for s in total)

            return {
                "total_questions": total_answered,
                "total_correct": total_correct,
                "total_duration": total_duration,
                "accuracy_rate": round(total_correct / total_answered * 100, 2) if total_answered > 0 else 0
            }
        finally:
            session.close()

    def get_streak_days(self) -> int:
        """获取连续学习天数"""
        session = self.get_session()
        try:
            stats = session.query(StudyStatistics).filter(
                StudyStatistics.questions_answered > 0
            ).order_by(StudyStatistics.stat_date.desc()).all()

            if not stats:
                return 0

            streak = 0
            today = date.today()
            expected_date = today

            for stat in stats:
                if stat.stat_date == expected_date:
                    streak += 1
                    expected_date -= timedelta(days=1)
                elif stat.stat_date == expected_date - timedelta(days=1):
                    streak += 1
                    expected_date = stat.stat_date
                else:
                    break

            return streak
        finally:
            session.close()

    def get_summary(self) -> Dict[str, Any]:
        """获取学习总结"""
        today = self.get_today_statistics()
        total = self.get_total_statistics()
        streak = self.get_streak_days()

        return {
            "today": today,
            "total": total,
            "streak_days": streak
        }

    def reset_today_statistics(self) -> bool:
        """重置今日统计"""
        session = self.get_session()
        try:
            today = date.today()
            stat = session.query(StudyStatistics).filter(
                StudyStatistics.stat_date == today
            ).first()

            if stat:
                stat.questions_answered = 0
                stat.correct_count = 0
                stat.wrong_count = 0
                stat.accuracy_rate = 0.0
                stat.study_duration = 0
                stat.review_count = 0
                stat.new_count = 0
                stat.update_time = datetime.now()
                session.commit()
                logger.info("今日统计已重置")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"重置今日统计失败: {e}")
            raise
        finally:
            session.close()

    def reset_all_statistics(self) -> int:
        """重置所有统计"""
        session = self.get_session()
        try:
            count = session.query(StudyStatistics).delete()
            session.commit()
            logger.info(f"所有统计已重置: {count}条记录")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"重置所有统计失败: {e}")
            raise
        finally:
            session.close()
