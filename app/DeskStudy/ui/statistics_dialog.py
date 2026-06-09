"""
学习统计对话框
"""

from PySide6 import QtWidgets, QtCore, QtGui

from app.DeskStudy.services.statistics_service import StatisticsService
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsDialog(QtWidgets.QDialog):
    """学习统计对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_service = StatisticsService()

        self._setup_ui()
        self._load_statistics()

        logger.info("统计对话框初始化完成")

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("📊 学习统计")
        self.setFixedSize(550, 480)
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
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #6366F1;
            }
            QTableWidget {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                gridline-color: rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item:selected {
                background: rgba(99, 102, 241, 0.3);
            }
            QHeaderView::section {
                background: rgba(99, 102, 241, 0.2);
                color: white;
                padding: 8px;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: bold;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QtWidgets.QLabel("📊 学习统计")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
        """)
        layout.addWidget(title)

        # 今日统计卡片
        today_group = QtWidgets.QGroupBox("今日统计")
        today_layout = QtWidgets.QVBoxLayout(today_group)

        self._today_table = QtWidgets.QTableWidget()
        self._today_table.setColumnCount(2)
        self._today_table.setHorizontalHeaderLabels(["指标", "数值"])
        self._today_table.horizontalHeader().setStretchLastSection(True)
        self._today_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._today_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._today_table.verticalHeader().setVisible(False)
        self._today_table.setRowCount(4)
        today_layout.addWidget(self._today_table)

        layout.addWidget(today_group)

        # 累计统计卡片
        total_group = QtWidgets.QGroupBox("累计统计")
        total_layout = QtWidgets.QVBoxLayout(total_group)

        self._total_table = QtWidgets.QTableWidget()
        self._total_table.setColumnCount(2)
        self._total_table.setHorizontalHeaderLabels(["指标", "数值"])
        self._total_table.horizontalHeader().setStretchLastSection(True)
        self._total_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._total_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._total_table.verticalHeader().setVisible(False)
        self._total_table.setRowCount(4)
        total_layout.addWidget(self._total_table)

        layout.addWidget(total_group)

        # 按钮区域
        btn_layout = QtWidgets.QHBoxLayout()

        self._reset_today_btn = QtWidgets.QPushButton("重置今日")
        self._reset_today_btn.setFixedHeight(36)
        self._reset_today_btn.setStyleSheet("""
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
        self._reset_today_btn.clicked.connect(self._on_reset_today)
        btn_layout.addWidget(self._reset_today_btn)

        self._reset_all_btn = QtWidgets.QPushButton("重置全部")
        self._reset_all_btn.setFixedHeight(36)
        self._reset_all_btn.setStyleSheet("""
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
        self._reset_all_btn.clicked.connect(self._on_reset_all)
        btn_layout.addWidget(self._reset_all_btn)

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

    def _load_statistics(self) -> None:
        """加载统计数据"""
        today = self._stats_service.get_today_statistics()
        total = self._stats_service.get_total_statistics()
        streak = self._stats_service.get_streak_days()

        # 今日统计
        today_data = [
            ("📝 答题数", str(today.get('questions_answered', 0))),
            ("✅ 正确数", str(today.get('correct_count', 0))),
            ("📈 正确率", f"{today.get('accuracy_rate', 0):.1f}%"),
            ("⏱ 学习时长", f"{today.get('study_duration', 0) // 60} 分钟"),
        ]

        for row, (label, value) in enumerate(today_data):
            label_item = QtWidgets.QTableWidgetItem(label)
            label_item.setForeground(QtGui.QColor("#9CA3AF"))
            self._today_table.setItem(row, 0, label_item)

            value_item = QtWidgets.QTableWidgetItem(value)
            value_item.setForeground(QtGui.QColor("#10B981"))
            value_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._today_table.setItem(row, 1, value_item)

        self._today_table.resizeColumnsToContents()

        # 累计统计
        total_data = [
            ("📚 总答题数", str(total.get('total_questions', 0))),
            ("🎯 总正确率", f"{total.get('accuracy_rate', 0):.1f}%"),
            ("⏰ 总学习时长", f"{total.get('total_duration', 0) // 60} 分钟"),
            ("🔥 连续学习", f"{streak} 天"),
        ]

        for row, (label, value) in enumerate(total_data):
            label_item = QtWidgets.QTableWidgetItem(label)
            label_item.setForeground(QtGui.QColor("#9CA3AF"))
            self._total_table.setItem(row, 0, label_item)

            value_item = QtWidgets.QTableWidgetItem(value)
            value_item.setForeground(QtGui.QColor("#6366F1"))
            value_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._total_table.setItem(row, 1, value_item)

        self._total_table.resizeColumnsToContents()

    def _on_reset_today(self) -> None:
        """重置今日统计"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认重置",
            "确定要重置今日的学习统计吗？\n此操作不可恢复！",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._stats_service.reset_today_statistics()
            self._load_statistics()
            QtWidgets.QMessageBox.information(self, "成功", "今日统计已重置")

    def _on_reset_all(self) -> None:
        """重置所有统计"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有的学习统计吗？\n此操作不可恢复！",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._stats_service.reset_all_statistics()
            self._load_statistics()
            QtWidgets.QMessageBox.information(self, "成功", "所有统计已重置")

    def showEvent(self, event) -> None:
        """窗口显示时重新加载数据"""
        super().showEvent(event)
        self._load_statistics()
