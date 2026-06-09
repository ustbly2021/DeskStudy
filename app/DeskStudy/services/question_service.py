"""
题库服务
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.DeskStudy.database.connection import get_database
from app.DeskStudy.models.question import Question
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class QuestionService:
    """题目服务"""

    def __init__(self):
        self.db = get_database()

    def get_session(self) -> Session:
        return self.db.get_session()

    def add_question(self, question_data: Dict[str, Any]) -> Question:
        """添加题目"""
        session = self.get_session()
        try:
            question = Question(
                content=question_data.get("content", ""),
                option_a=question_data.get("option_a", ""),
                option_b=question_data.get("option_b", ""),
                option_c=question_data.get("option_c"),
                option_d=question_data.get("option_d"),
                correct_answer=question_data.get("correct_answer", "").upper(),
                explanation=question_data.get("explanation"),
                category=question_data.get("category"),
                correct_rate=question_data.get("correct_rate", 0.0),
                source=question_data.get("source"),
                question_type=question_data.get("question_type", "single"),
                is_judgment=question_data.get("is_judgment", False)
            )
            session.add(question)
            session.commit()
            session.refresh(question)
            logger.info(f"添加题目成功: ID={question.id}")
            return question
        except Exception as e:
            session.rollback()
            logger.error(f"添加题目失败: {e}")
            raise
        finally:
            session.close()

    def add_questions_batch(self, questions_data: List[Dict[str, Any]]) -> int:
        """批量添加题目"""
        session = self.get_session()
        count = 0
        try:
            for q_data in questions_data:
                question = Question(
                    content=q_data.get("content", ""),
                    option_a=q_data.get("option_a", ""),
                    option_b=q_data.get("option_b", ""),
                    option_c=q_data.get("option_c"),
                    option_d=q_data.get("option_d"),
                    correct_answer=q_data.get("correct_answer", "").upper(),
                    explanation=q_data.get("explanation"),
                    category=q_data.get("category"),
                    correct_rate=q_data.get("correct_rate", 0.0),
                    source=q_data.get("source"),
                    question_type=q_data.get("question_type", "single"),
                    is_judgment=q_data.get("is_judgment", False)
                )
                session.add(question)
                count += 1

            session.commit()
            logger.info(f"批量添加题目成功: {count}题")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"批量添加题目失败: {e}")
            raise
        finally:
            session.close()

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """根据ID获取题目"""
        session = self.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if question:
                # 在 session 关闭前访问属性，确保数据加载
                _ = question.content
                _ = question.correct_answer
                _ = question.category
                _ = question.option_a
                _ = question.option_b
                _ = question.option_c
                _ = question.option_d
                _ = question.explanation
                _ = question.is_judgment
            return question
        finally:
            session.close()

    def get_all_questions(self, category: Optional[str] = None) -> List[Question]:
        """获取所有题目"""
        session = self.get_session()
        try:
            query = session.query(Question)
            if category:
                query = query.filter(Question.category == category)
            questions = query.all()
            # 在 session 关闭前访问属性
            for q in questions:
                _ = q.content
                _ = q.correct_answer
            return questions
        finally:
            session.close()

    def get_random_question(
        self,
        exclude_id: Optional[int] = None
    ) -> Optional[Question]:
        """获取随机题目"""
        from random import choice
        session = self.get_session()
        try:
            query = session.query(Question)
            if exclude_id:
                query = query.filter(Question.id != exclude_id)
            questions = query.all()
            if questions:
                q = choice(questions)
                # 在 session 关闭前访问属性
                _ = q.content
                _ = q.correct_answer
                _ = q.category
                _ = q.option_a
                _ = q.option_b
                _ = q.option_c
                _ = q.option_d
                _ = q.explanation
                _ = q.is_judgment
                return q
            return None
        finally:
            session.close()

    def get_questions_by_ids(self, question_ids: List[int]) -> List[Question]:
        """根据ID列表获取题目"""
        session = self.get_session()
        try:
            questions = session.query(Question).filter(Question.id.in_(question_ids)).all()
            # 在 session 关闭前访问属性
            for q in questions:
                _ = q.content
                _ = q.correct_answer
            return questions
        finally:
            session.close()

    def update_question(self, question_id: int, question_data: Dict[str, Any]) -> Optional[Question]:
        """更新题目"""
        session = self.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if question:
                for key, value in question_data.items():
                    if hasattr(question, key):
                        setattr(question, key, value)
                question.update_time = datetime.now()
                session.commit()
                session.refresh(question)
                logger.info(f"更新题目成功: ID={question_id}")
            return question
        except Exception as e:
            session.rollback()
            logger.error(f"更新题目失败: {e}")
            raise
        finally:
            session.close()

    def delete_question(self, question_id: int) -> bool:
        """删除题目"""
        session = self.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if question:
                session.delete(question)
                session.commit()
                logger.info(f"删除题目成功: ID={question_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除题目失败: {e}")
            raise
        finally:
            session.close()

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        session = self.get_session()
        try:
            results = session.query(Question.category).distinct().all()
            return [r[0] for r in results if r[0]]
        finally:
            session.close()

    def import_from_json(self, file_path: str) -> int:
        """从JSON文件导入题库"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            questions_data = data
        elif isinstance(data, dict) and "questions" in data:
            questions_data = data["questions"]
        else:
            raise ValueError("JSON格式错误")

        return self.add_questions_batch(questions_data)

    def import_questions(self, questions: List[Dict[str, Any]]) -> int:
        """
        直接导入题目列表

        Args:
            questions: 题目列表，每个题目为字典格式

        Returns:
            导入的题目数量
        """
        return self.add_questions_batch(questions)

    def export_to_json(self, file_path: str, category: Optional[str] = None) -> int:
        """导出题库到JSON文件"""
        questions = self.get_all_questions(category)
        data = [q.to_dict() for q in questions]

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"导出题库成功: {len(data)}题")
        return len(data)

    def get_statistics(self) -> Dict[str, Any]:
        """获取题库统计"""
        session = self.get_session()
        try:
            total = session.query(Question).count()
            categories = self.get_categories()
            return {
                "total": total,
                "categories": categories,
                "category_count": len(categories)
            }
        finally:
            session.close()

    def clear_all(self) -> int:
        """清空所有题目"""
        session = self.get_session()
        try:
            count = session.query(Question).count()
            session.query(Question).delete()
            session.commit()
            logger.info(f"清空题库成功: 删除{count}题")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"清空题库失败: {e}")
            raise
        finally:
            session.close()
