"""
错题本窗口
"""

from typing import List, Optional

from PySide6 import QtWidgets, QtCore, QtGui

from app.DeskStudy.services.wrong_question_service import WrongQuestionService
from app.DeskStudy.services.question_service import QuestionService
from app.DeskStudy.models.wrong_question import WrongQuestion
from app.DeskStudy.models.question import Question
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class WrongQuestionDialog(QtWidgets.QDialog):
    """错题本对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._wrong_service = WrongQuestionService()
        self._question_service = QuestionService()

        self._setup_ui()
        self._load_wrong_questions()

        logger.info("错题本窗口初始化完成")

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("错题本")
        self.setFixedSize(600, 500)
        self.setWindowFlags(
            QtCore.Qt.Dialog |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowStaysOnTopHint
        )

        self.setStyleSheet("""
            QDialog {
                background: #1E1E28;
            }
            QWidget {
                color: white;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QtWidgets.QLabel("📚 错题本")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
            }
        """)
        layout.addWidget(title)

        # 统计信息
        self._stats_label = QtWidgets.QLabel()
        self._stats_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(self._stats_label)

        # 错题列表
        self._list_widget = QtWidgets.QListWidget()
        self._list_widget.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                background: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                padding: 10px;
                color: white;
            }
            QListWidget::item:selected {
                background: rgba(99, 102, 241, 0.3);
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        layout.addWidget(self._list_widget)

        # 详情区域
        self._detail_text = QtWidgets.QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setMaximumHeight(120)
        self._detail_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                color: #9CA3AF;
                font-size: 12px;
            }
        """)
        self._detail_text.setPlaceholderText("选择一道错题查看详情...")
        layout.addWidget(self._detail_text)

        # 按钮区域
        btn_layout = QtWidgets.QHBoxLayout()

        self._delete_btn = QtWidgets.QPushButton("删除选中")
        self._delete_btn.setFixedHeight(36)
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: #6B7280;
                border-color: #6B7280;
            }
        """)
        self._delete_btn.clicked.connect(self._delete_selected)
        self._delete_btn.setEnabled(False)
        btn_layout.addWidget(self._delete_btn)

        self._clear_btn = QtWidgets.QPushButton("清空错题本")
        self._clear_btn.setFixedHeight(36)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        self._clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(self._clear_btn)

        btn_layout.addStretch()

        self._close_btn = QtWidgets.QPushButton("关闭")
        self._close_btn.setFixedHeight(36)
        self._close_btn.setFixedWidth(80)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #818CF8;
            }
        """)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

        # 连接信号
        self._list_widget.currentRowChanged.connect(self._on_item_selected)

    def showEvent(self, event) -> None:
        """窗口显示时重新加载数据"""
        super().showEvent(event)
        self._load_wrong_questions()

    def _load_wrong_questions(self) -> None:
        """加载错题列表"""
        self._list_widget.clear()
        self._wrong_questions = self._wrong_service.get_all_wrong_questions()

        # 更新统计
        self._stats_label.setText(f"共 {len(self._wrong_questions)} 道错题")

        for wrong in self._wrong_questions:
            question = self._question_service.get_question_by_id(wrong.question_id)
            if question:
                # 截取题干前50字符
                content = question.content[:50] + "..." if len(question.content) > 50 else question.content
                item_text = f"[{question.category or '未分类'}] {content} (错{wrong.wrong_count}次)"
                item = QtWidgets.QListWidgetItem(item_text)
                item.setData(QtCore.Qt.UserRole, wrong.id)
                self._list_widget.addItem(item)

        self._detail_text.clear()
        self._delete_btn.setEnabled(False)

    def _on_item_selected(self, row: int) -> None:
        """选中错题"""
        if row < 0 or row >= len(self._wrong_questions):
            return

        wrong = self._wrong_questions[row]
        question = self._question_service.get_question_by_id(wrong.question_id)

        if question:
            detail = f"题目：{question.content}\n\n"
            # 添加选项
            if question.is_judgment:
                detail += "A. 正确\nB. 错误\n\n"
            else:
                if question.option_a:
                    detail += f"A. {question.option_a}\n"
                if question.option_b:
                    detail += f"B. {question.option_b}\n"
                if question.option_c:
                    detail += f"C. {question.option_c}\n"
                if question.option_d:
                    detail += f"D. {question.option_d}\n"
                detail += "\n"
            detail += f"正确答案：{question.correct_answer}\n"
            detail += f"你的错误答案：{wrong.wrong_answer}\n"
            detail += f"错误次数：{wrong.wrong_count} 次\n"
            if question.explanation:
                detail += f"\n解析：{question.explanation}"
            self._detail_text.setText(detail)

        self._delete_btn.setEnabled(True)

    def _delete_selected(self) -> None:
        """删除选中的错题"""
        row = self._list_widget.currentRow()
        if row < 0:
            return

        wrong = self._wrong_questions[row]
        reply = self._show_confirm("确认删除", "确定要从错题本中删除这道题吗？")

        if reply:
            self._wrong_service.remove_wrong_question(wrong.question_id)
            self._load_wrong_questions()
            self._show_message("成功", "已从错题本中删除", "success")

    def _clear_all(self) -> None:
        """清空错题本"""
        if not self._wrong_questions:
            self._show_message("提示", "错题本已经是空的", "info")
            return

        reply = self._show_confirm(
            "确认清空",
            f"确定要清空所有 {len(self._wrong_questions)} 道错题吗？\n此操作不可恢复！"
        )

        if reply:
            self._wrong_service.clear_all_wrong_questions()
            self._load_wrong_questions()
            self._show_message("成功", "错题本已清空", "success")

    def _show_message(self, title: str, message: str, msg_type: str = "info") -> None:
        """显示深色主题消息框"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if msg_type == "success":
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
        else:
            msg_box.setIcon(QtWidgets.QMessageBox.Information)

        # 设置深色主题样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #1E1E28;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #5558E3;
            }
        """)

        msg_box.exec()

    def _show_confirm(self, title: str, message: str) -> bool:
        """显示深色主题确认框"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)

        # 添加按钮
        yes_btn = msg_box.addButton("确定", QtWidgets.QMessageBox.AcceptRole)
        no_btn = msg_box.addButton("取消", QtWidgets.QMessageBox.RejectRole)

        # 设置深色主题样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #1E1E28;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #5558E3;
            }
        """)

        msg_box.exec()

        return msg_box.clickedButton() == yes_btn
