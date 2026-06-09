"""
题目卡片组件
"""

from typing import Optional, List

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from app.DeskStudy.config.settings import get_settings
from app.DeskStudy.models.question import Question
from app.DeskStudy.services.question_service import QuestionService
from app.DeskStudy.services.wrong_question_service import WrongQuestionService
from app.DeskStudy.services.review_service import ReviewService
from app.DeskStudy.services.statistics_service import StatisticsService
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)

# 面板尺寸常量
PANEL_WIDTH = 400
PANEL_MIN_HEIGHT = 300
PANEL_MAX_HEIGHT = 700


class OptionButton(QtWidgets.QWidget):
    """选项按钮 - 使用QLabel实现自动换行"""

    clicked = QtCore.Signal(str)

    def __init__(self, text: str, option_key: str, parent=None):
        super().__init__(parent)
        self.option_key = option_key
        self._selected = False
        self._correct = False
        self._setup_ui(text)

    def _setup_ui(self, text: str) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(0)

        self._label = QtWidgets.QLabel(text)
        self._label.setWordWrap(True)
        self._label.setMinimumHeight(20)
        self._label.setStyleSheet("color: white; font-size: 12px; background: transparent; line-height: 1.5;")
        layout.addWidget(self._label)

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._apply_style()

    def _apply_style(self) -> None:
        if self._correct:
            self.setStyleSheet("""
                QWidget {
                    background: rgba(16, 185, 129, 0.3);
                    border: 1px solid #10B981;
                    border-radius: 6px;
                }
                QLabel {
                    color: #10B981;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        elif self._selected:
            self.setStyleSheet("""
                QWidget {
                    background: rgba(239, 68, 68, 0.3);
                    border: 1px solid #EF4444;
                    border-radius: 6px;
                }
                QLabel {
                    color: #EF4444;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                }
                QWidget:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.2);
                }
                QLabel {
                    color: white;
                    font-size: 12px;
                }
            """)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def set_correct(self, correct: bool) -> None:
        self._correct = correct
        self._apply_style()

    def mousePressEvent(self, event) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.option_key)
        super().mousePressEvent(event)


class ExplanationWidget(QtWidgets.QWidget):
    """解析显示组件，支持展开/收起，展开后用滚动区域"""

    expand_changed = QtCore.Signal()  # 展开/收起状态变化信号
    MAX_EXPAND_HEIGHT = 200  # 展开后最大高度，超出滚动

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self._max_collapsed_lines = 3
        self._full_text = ''
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 折叠时用的标签
        self._text_label = QtWidgets.QLabel()
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 11px;
                background: rgba(255, 255, 255, 0.05);
                padding: 8px;
                border-radius: 6px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self._text_label)

        # 展开时用的滚动区域
        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMaximumHeight(self.MAX_EXPAND_HEIGHT)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self._scroll_label = QtWidgets.QLabel()
        self._scroll_label.setWordWrap(True)
        self._scroll_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 11px;
                padding: 8px;
                line-height: 1.5;
                background: transparent;
            }
        """)
        self._scroll_area.setWidget(self._scroll_label)
        self._scroll_area.hide()
        layout.addWidget(self._scroll_area)

        self._expand_btn = QtWidgets.QPushButton("展开解析 ▼")
        self._expand_btn.setFixedHeight(24)
        self._expand_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._expand_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6366F1;
                border: none;
                font-size: 11px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                color: #818CF8;
            }
        """)
        self._expand_btn.clicked.connect(self._toggle_expand)
        self._expand_btn.hide()
        layout.addWidget(self._expand_btn, alignment=QtCore.Qt.AlignRight)

    def set_text(self, text: str) -> None:
        self._full_text = text
        self._text_label.setText(text)
        self._scroll_label.setText(text)
        self._text_label.setMaximumHeight(16777215)

        font_metrics = self._text_label.fontMetrics()
        line_height = font_metrics.lineSpacing()
        text_height = font_metrics.boundingRect(
            0, 0, PANEL_WIDTH - 56, 0,
            QtCore.Qt.TextWordWrap, text
        ).height()

        if text_height > line_height * self._max_collapsed_lines:
            self._expand_btn.show()
            self._collapse()
        else:
            self._expand_btn.hide()

    def _collapse(self) -> None:
        self._is_expanded = False
        self._scroll_area.hide()
        self._text_label.show()
        font_metrics = self._text_label.fontMetrics()
        line_height = font_metrics.lineSpacing()
        max_h = int(line_height * (self._max_collapsed_lines + 0.5)) + 20
        self._text_label.setMaximumHeight(max_h)
        self._expand_btn.setText("展开解析 ▼")

    def _expand(self) -> None:
        self._is_expanded = True
        self._text_label.hide()
        self._scroll_area.show()
        self._scroll_label.updateGeometry()
        self._expand_btn.setText("收起解析 ▲")

    def _toggle_expand(self) -> None:
        if self._is_expanded:
            self._collapse()
        else:
            self._expand()
        self.expand_changed.emit()

    def clear(self) -> None:
        self._text_label.setText("")
        self._text_label.setMaximumHeight(16777215)
        self._scroll_label.setText("")
        self._scroll_area.hide()
        self._text_label.show()
        self._expand_btn.hide()


class QuestionCard(QtWidgets.QFrame):
    """题目卡片"""

    answer_signal = QtCore.Signal(bool)
    size_changed = QtCore.Signal()

    def __init__(
        self,
        question_service: QuestionService,
        wrong_service: WrongQuestionService,
        review_service: ReviewService,
        stats_service: StatisticsService,
        parent=None
    ):
        super().__init__(parent)
        self._question_service = question_service
        self._wrong_service = wrong_service
        self._review_service = review_service
        self._stats_service = stats_service

        self._current_question: Optional[Question] = None
        self._option_buttons: List[OptionButton] = []
        self._answered = False
        self._is_review_mode = False  # False=刷题模式, True=复盘模式

        self._setup_ui()
        logger.info("题目卡片初始化完成")

    def set_review_mode(self, is_review: bool) -> None:
        """设置模式"""
        self._is_review_mode = is_review
        logger.info(f"切换到{'复盘' if is_review else '刷题'}模式")

    def _setup_ui(self) -> None:
        """设置UI - 简洁布局，固定宽度，高度自适应"""
        self.setFixedWidth(PANEL_WIDTH)
        self.setStyleSheet("""
            QFrame {
                background: rgba(30, 30, 40, 220);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # 主布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # 顶部信息栏：分类 + 来源 + 正确率
        self._top_info_layout = QtWidgets.QHBoxLayout()
        self._top_info_layout.setSpacing(8)

        self._category_label = QtWidgets.QLabel()
        self._category_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 10px;
            }
        """)
        self._top_info_layout.addWidget(self._category_label)

        self._source_label = QtWidgets.QLabel()
        self._source_label.setStyleSheet("""
            QLabel {
                color: #818CF8;
                font-size: 10px;
            }
        """)
        self._top_info_layout.addWidget(self._source_label)

        self._correct_rate_label = QtWidgets.QLabel()
        self._correct_rate_label.setStyleSheet("""
            QLabel {
                color: #10B981;
                font-size: 10px;
            }
        """)
        self._top_info_layout.addWidget(self._correct_rate_label)

        self._top_info_layout.addStretch()
        layout.addLayout(self._top_info_layout)

        # 题干
        self._question_label = QtWidgets.QLabel()
        self._question_label.setWordWrap(True)
        self._question_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                line-height: 1.5;
                padding: 2px 0px;
            }
        """)
        layout.addWidget(self._question_label)

        # 选项区域
        self._options_layout = QtWidgets.QVBoxLayout()
        self._options_layout.setSpacing(6)
        layout.addLayout(self._options_layout)

        # 解析区域
        self._explanation_widget = ExplanationWidget(self)
        self._explanation_widget.hide()
        self._explanation_widget.expand_changed.connect(
            lambda: QtCore.QTimer.singleShot(50, self._adjust_size)
        )
        layout.addWidget(self._explanation_widget)

        # 底部：结果 + 下一题按钮
        self._bottom_layout = QtWidgets.QHBoxLayout()
        self._bottom_layout.addStretch()

        self._result_icon = QtWidgets.QLabel()
        self._result_icon.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self._bottom_layout.addWidget(self._result_icon)

        self._next_btn = QtWidgets.QPushButton("下一题 →")
        self._next_btn.setFixedSize(80, 28)
        self._next_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._next_btn.setStyleSheet("""
            QPushButton {
                background: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #818CF8;
            }
        """)
        self._next_btn.clicked.connect(self._load_next_question)
        self._next_btn.hide()
        self._bottom_layout.addWidget(self._next_btn)

        layout.addLayout(self._bottom_layout)

    def _clear_options(self) -> None:
        while self._options_layout.count():
            item = self._options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._option_buttons.clear()

    def _create_option_button(self, text: str, key: str) -> OptionButton:
        label = f"{key}. {text}"
        btn = OptionButton(label, key, self)
        btn.clicked.connect(lambda k=key: self._on_option_clicked(k))
        return btn

    def _load_next_question(self) -> None:
        """加载下一题"""
        self._answered = False
        self._explanation_widget.hide()
        self._explanation_widget.clear()
        self._result_icon.setText("")
        self._next_btn.hide()

        if self._is_review_mode:
            # 复盘模式：从错题本获取题目
            wrong_questions = self._wrong_service.get_wrong_questions_for_review(limit=10)
            if wrong_questions:
                from random import choice
                wrong = choice(wrong_questions)
                self._current_question = self._question_service.get_question_by_id(wrong.question_id)
            else:
                self._current_question = None
        else:
            # 刷题模式：从题库随机获取题目
            exclude_id = self._current_question.id if self._current_question else None
            self._current_question = self._question_service.get_random_question(exclude_id)

        if not self._current_question:
            mode_text = "错题本为空" if self._is_review_mode else "题库为空"
            self._question_label.setText(mode_text)
            self._clear_options()
            self._category_label.setText("")
            self._source_label.setText("")
            self._correct_rate_label.setText("")
            return

        self._question_label.setText(self._current_question.content)

        # 设置分类标签
        mode_tag = "[复盘]" if self._is_review_mode else ""
        self._category_label.setText(f"{mode_tag}[{self._current_question.category or '未分类'}]")

        # 设置来源标签
        source = getattr(self._current_question, 'source', None)
        if source:
            self._source_label.setText(f"📍 {source}")
        else:
            self._source_label.setText("")

        # 设置正确率标签
        correct_rate = getattr(self._current_question, 'correct_rate', None)
        if correct_rate and correct_rate > 0:
            self._correct_rate_label.setText(f"✓ {correct_rate:.0f}%")
        else:
            self._correct_rate_label.setText("")

        self._clear_options()

        if self._current_question.is_judgment:
            for key, text in [("A", "正确"), ("B", "错误")]:
                btn = self._create_option_button(text, key)
                self._options_layout.addWidget(btn)
                self._option_buttons.append(btn)
        else:
            options = [
                ("A", self._current_question.option_a),
                ("B", self._current_question.option_b),
                ("C", self._current_question.option_c),
                ("D", self._current_question.option_d),
            ]
            for key, text in options:
                if text:
                    btn = self._create_option_button(text, key)
                    self._options_layout.addWidget(btn)
                    self._option_buttons.append(btn)

        logger.debug(f"加载题目: ID={self._current_question.id}")
        # 延迟调整大小，等布局完成
        QtCore.QTimer.singleShot(50, self._adjust_size)

    def _on_option_clicked(self, key: str) -> None:
        """选项点击处理"""
        if self._answered or not self._current_question:
            return

        self._answered = True
        correct = key.upper() == self._current_question.correct_answer.upper()

        for btn in self._option_buttons:
            if btn.option_key.upper() == self._current_question.correct_answer.upper():
                btn.set_correct(True)
            elif btn.option_key == key and not correct:
                btn.set_selected(True)

        if correct:
            self._result_icon.setText("✔ 正确")
            self._result_icon.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #10B981;
                    font-weight: bold;
                }
            """)
            self._stats_service.record_answer(correct=True)
        else:
            self._result_icon.setText("✘ 错误")
            self._result_icon.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #EF4444;
                    font-weight: bold;
                }
            """)
            self._stats_service.record_answer(correct=False)
            # 添加到错题本
            try:
                self._wrong_service.add_wrong_question(
                    self._current_question.id, key
                )
                logger.info(f"已添加到错题本: question_id={self._current_question.id}")
            except Exception as e:
                logger.error(f"添加错题失败: {e}")

        explanation = self._current_question.explanation
        if explanation:
            self._explanation_widget.set_text(explanation)
            self._explanation_widget.show()

        self._next_btn.show()
        QtCore.QTimer.singleShot(50, self._adjust_size)
        logger.info(f"答题结果: {'正确' if correct else '错误'}")

    def _adjust_size(self) -> None:
        """根据内容自适应调整高度"""
        # 让布局重新计算
        self.updateGeometry()
        self.layout().activate()

        # 逐个组件累加高度
        total_height = 32  # 上下边距
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and item.widget().isVisible():
                widget = item.widget()
                widget.updateGeometry()
                total_height += widget.sizeHint().height() + 8  # spacing
            elif item.layout():
                sub_layout = item.layout()
                for j in range(sub_layout.count()):
                    sub_item = sub_layout.itemAt(j)
                    if sub_item.widget() and sub_item.widget().isVisible():
                        sub_item.widget().updateGeometry()
                        total_height += sub_item.widget().sizeHint().height() + 6

        total_height = max(PANEL_MIN_HEIGHT, min(total_height, PANEL_MAX_HEIGHT))
        self.setFixedHeight(total_height)
        self.size_changed.emit()

    def refresh(self) -> None:
        self._load_next_question()
