"""
设置窗口
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from app.DeskStudy.config.settings import Settings, get_settings, save_settings
from app.DeskStudy.services.question_service import QuestionService
from app.DeskStudy.utils.logger import get_logger
from app.DeskStudy.ui.fenbi_import_dialog import FenbiImportDialog

logger = get_logger(__name__)

JSON_FILTER = "JSON Files (*.json);;All Files (*.*)"
JSON_SAVE_FILTER = "JSON Files (*.json)"

CHECKBOX_STYLE = """
    QCheckBox {
        color: white;
        spacing: 8px;
        background: transparent;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.1);
    }
    QCheckBox::indicator:checked {
        background: #6366F1;
        border-color: #6366F1;
    }
"""

SLIDER_STYLE = """
    QSlider {
        background: transparent;
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 16px;
        background: #6366F1;
        border-radius: 8px;
        margin: -6px 0;
    }
"""


class SettingsDialog(QtWidgets.QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings()
        self._question_service = QuestionService()

        self._setup_ui()
        self._load_settings()

        logger.info("设置窗口初始化完成")

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("设置")
        self.setFixedSize(620, 520)
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
                background: transparent;
                color: white;
            }
            QLabel {
                color: white;
                background: transparent;
            }
            QGroupBox {
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: white;
            }
            QFormLayout {
                background: transparent;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)

        content = QtWidgets.QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setSpacing(16)

        self._create_floating_ball_settings(content_layout)
        self._create_hotkey_settings(content_layout)
        self._create_study_settings(content_layout)
        self._create_question_bank_settings(content_layout)
        self._create_general_settings(content_layout)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        self._save_btn = QtWidgets.QPushButton("保存")
        self._save_btn.setFixedSize(100, 36)
        self._save_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._save_btn.setStyleSheet("""
            QPushButton {
                background: #6366F1;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5558E3;
            }
        """)
        self._save_btn.clicked.connect(self._on_save)

        self._cancel_btn = QtWidgets.QPushButton("取消")
        self._cancel_btn.setFixedSize(100, 36)
        self._cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self._cancel_btn)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _create_floating_ball_settings(self, parent_layout) -> None:
        """创建悬浮球设置"""
        group = QtWidgets.QGroupBox("悬浮球设置")

        layout = QtWidgets.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        layout.setSpacing(12)

        self._size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._size_slider.setMinimum(40)
        self._size_slider.setMaximum(70)
        self._size_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self._size_slider.setTickInterval(8)
        self._size_slider.setFixedWidth(200)
        self._size_slider.setStyleSheet(SLIDER_STYLE)

        self._size_label = QtWidgets.QLabel("40")
        self._size_label.setFixedWidth(30)
        size_layout = QtWidgets.QHBoxLayout()
        size_layout.addWidget(self._size_slider)
        size_layout.addWidget(self._size_label)
        layout.addRow("悬浮球大小:", size_layout)

        self._opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._opacity_slider.setMinimum(10)
        self._opacity_slider.setMaximum(100)
        self._opacity_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self._opacity_slider.setTickInterval(10)
        self._opacity_slider.setFixedWidth(200)
        self._opacity_slider.setStyleSheet(SLIDER_STYLE)

        self._opacity_label = QtWidgets.QLabel("90%")
        self._opacity_label.setFixedWidth(40)
        opacity_layout = QtWidgets.QHBoxLayout()
        opacity_layout.addWidget(self._opacity_slider)
        opacity_layout.addWidget(self._opacity_label)
        layout.addRow("透明度:", opacity_layout)

        self._auto_hide_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._auto_hide_slider.setMinimum(1000)
        self._auto_hide_slider.setMaximum(10000)
        self._auto_hide_slider.setTickInterval(1000)
        self._auto_hide_slider.setFixedWidth(200)
        self._auto_hide_slider.setStyleSheet(SLIDER_STYLE)

        self._auto_hide_label = QtWidgets.QLabel("3000ms")
        self._auto_hide_label.setFixedWidth(60)
        auto_hide_layout = QtWidgets.QHBoxLayout()
        auto_hide_layout.addWidget(self._auto_hide_slider)
        auto_hide_layout.addWidget(self._auto_hide_label)
        layout.addRow("自动隐藏:", auto_hide_layout)

        self._edge_snap_cb = QtWidgets.QCheckBox("启用边缘吸附")
        self._edge_snap_cb.setStyleSheet(CHECKBOX_STYLE)
        layout.addRow("", self._edge_snap_cb)

        self._mouse_penetrate_cb = QtWidgets.QCheckBox("启用鼠标穿透")
        self._mouse_penetrate_cb.setStyleSheet(CHECKBOX_STYLE)
        layout.addRow("", self._mouse_penetrate_cb)

        self._size_slider.valueChanged.connect(
            lambda v: self._size_label.setText(str(v))
        )
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        self._auto_hide_slider.valueChanged.connect(
            lambda v: self._auto_hide_label.setText(f"{v}ms")
        )

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_hotkey_settings(self, parent_layout) -> None:
        """创建热键设置"""
        group = QtWidgets.QGroupBox("快捷键设置")

        layout = QtWidgets.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        layout.setSpacing(12)

        self._boss_key_input = QtWidgets.QLineEdit()
        self._boss_key_input.setFixedWidth(200)
        self._boss_key_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: #6366F1;
            }
        """)
        layout.addRow("老板键:", self._boss_key_input)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_study_settings(self, parent_layout) -> None:
        """创建学习设置"""
        group = QtWidgets.QGroupBox("学习设置")

        layout = QtWidgets.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        layout.setSpacing(12)

        self._interval_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._interval_slider.setMinimum(1000)
        self._interval_slider.setMaximum(5000)
        self._interval_slider.setTickInterval(500)
        self._interval_slider.setFixedWidth(200)
        self._interval_slider.setStyleSheet(SLIDER_STYLE)

        self._interval_label = QtWidgets.QLabel("2000ms")
        self._interval_label.setFixedWidth(60)
        interval_layout = QtWidgets.QHBoxLayout()
        interval_layout.addWidget(self._interval_slider)
        interval_layout.addWidget(self._interval_label)
        layout.addRow("自动下一题:", interval_layout)

        self._show_explanation_cb = QtWidgets.QCheckBox("显示解析")
        self._show_explanation_cb.setStyleSheet(CHECKBOX_STYLE)
        self._show_explanation_cb.setChecked(True)
        layout.addRow("", self._show_explanation_cb)

        self._interval_slider.valueChanged.connect(
            lambda v: self._interval_label.setText(f"{v}ms")
        )

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_question_bank_settings(self, parent_layout) -> None:
        """创建题库设置"""
        group = QtWidgets.QGroupBox("题库管理")

        layout = QtWidgets.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        layout.setSpacing(12)

        stats = self._question_service.get_statistics()

        self._stats_label = QtWidgets.QLabel(
            f"题目总数: {stats.get('total', 0)} | "
            f"分类数: {stats.get('category_count', 0)}"
        )
        self._stats_label.setStyleSheet("color: #9CA3AF; font-weight: normal; background: transparent;")
        layout.addRow("题库状态:", self._stats_label)

        # 按钮样式
        btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15), stop:1 rgba(255, 255, 255, 0.05));
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25), stop:1 rgba(255, 255, 255, 0.1));
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """

        fenbi_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(99, 102, 241, 0.4), stop:1 rgba(99, 102, 241, 0.2));
                color: white;
                border: 1px solid rgba(99, 102, 241, 0.5);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(99, 102, 241, 0.5), stop:1 rgba(99, 102, 241, 0.3));
                border-color: rgba(99, 102, 241, 0.7);
            }
            QPushButton:pressed {
                background: rgba(99, 102, 241, 0.3);
            }
        """

        clear_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(239, 68, 68, 0.3), stop:1 rgba(239, 68, 68, 0.15));
                color: #FCA5A5;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(239, 68, 68, 0.4), stop:1 rgba(239, 68, 68, 0.2));
                border-color: rgba(239, 68, 68, 0.6);
            }
            QPushButton:pressed {
                background: rgba(239, 68, 68, 0.2);
            }
        """

        import_btn = QtWidgets.QPushButton("📥 导入")
        import_btn.setFixedHeight(32)
        import_btn.setCursor(QtCore.Qt.PointingHandCursor)
        import_btn.setStyleSheet(btn_style)
        import_btn.clicked.connect(self._on_import)

        fenbi_btn = QtWidgets.QPushButton("🌐 粉笔导入")
        fenbi_btn.setFixedHeight(32)
        fenbi_btn.setCursor(QtCore.Qt.PointingHandCursor)
        fenbi_btn.setStyleSheet(fenbi_style)
        fenbi_btn.clicked.connect(self._on_fenbi_import)

        export_btn = QtWidgets.QPushButton("📤 导出")
        export_btn.setFixedHeight(32)
        export_btn.setCursor(QtCore.Qt.PointingHandCursor)
        export_btn.setStyleSheet(btn_style)
        export_btn.clicked.connect(self._on_export)

        clear_btn = QtWidgets.QPushButton("🗑 清空")
        clear_btn.setFixedHeight(32)
        clear_btn.setCursor(QtCore.Qt.PointingHandCursor)
        clear_btn.setStyleSheet(clear_style)
        clear_btn.clicked.connect(self._on_clear)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(fenbi_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addRow("操作:", btn_layout)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_general_settings(self, parent_layout) -> None:
        """创建通用设置"""
        group = QtWidgets.QGroupBox("通用设置")

        layout = QtWidgets.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        layout.setSpacing(12)

        self._auto_start_cb = QtWidgets.QCheckBox("开机启动")
        self._auto_start_cb.setStyleSheet(CHECKBOX_STYLE)
        layout.addRow("", self._auto_start_cb)

        self._mute_cb = QtWidgets.QCheckBox("静默模式（全屏时暂停）")
        self._mute_cb.setStyleSheet(CHECKBOX_STYLE)
        self._mute_cb.setChecked(True)
        layout.addRow("", self._mute_cb)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _load_settings(self) -> None:
        """加载设置"""
        fb = self._settings.floating_ball
        hotkey = self._settings.hotkey
        study = self._settings.study

        self._size_slider.setValue(fb.size)
        self._opacity_slider.setValue(int(fb.opacity * 100))
        self._auto_hide_slider.setValue(fb.auto_hide_delay)
        self._edge_snap_cb.setChecked(fb.edge_snap_enabled)
        self._mouse_penetrate_cb.setChecked(fb.mouse_penetrate)

        self._boss_key_input.setText(hotkey.boss_key)

        self._interval_slider.setValue(study.auto_next_delay)
        self._show_explanation_cb.setChecked(study.show_explanation)

        self._auto_start_cb.setChecked(self._settings.auto_start)
        self._mute_cb.setChecked(self._settings.mute_mode)

    def _on_save(self) -> None:
        """保存设置"""
        fb = self._settings.floating_ball
        hotkey = self._settings.hotkey
        study = self._settings.study

        fb.size = self._size_slider.value()
        fb.opacity = self._opacity_slider.value() / 100
        fb.auto_hide_delay = self._auto_hide_slider.value()
        fb.edge_snap_enabled = self._edge_snap_cb.isChecked()
        fb.mouse_penetrate = self._mouse_penetrate_cb.isChecked()

        hotkey.boss_key = self._boss_key_input.text()

        study.auto_next_delay = self._interval_slider.value()
        study.show_explanation = self._show_explanation_cb.isChecked()

        self._settings.auto_start = self._auto_start_cb.isChecked()
        self._settings.mute_mode = self._mute_cb.isChecked()

        save_settings(self._settings)
        logger.info("设置已保存")

        self.accept()

    def _on_import(self) -> None:
        """导入题库"""
        try:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "选择题库文件",
                "",
                JSON_FILTER
            )
            if not file_path:
                return
            count = self._question_service.import_from_json(file_path)
            QtWidgets.QMessageBox.information(
                self,
                "导入成功",
                f"成功导入 {count} 道题目"
            )
            stats = self._question_service.get_statistics()
            self._stats_label.setText(
                f"题目总数: {stats.get('total', 0)} | "
                f"分类数: {stats.get('category_count', 0)}"
            )
            logger.info(f"导入题库: {file_path}, 共{count}题")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "导入失败",
                f"导入题库失败: {str(e)}"
            )
            logger.error(f"导入题库失败: {e}")

    def _on_fenbi_import(self) -> None:
        """从粉笔网导入题目"""
        try:
            dialog = FenbiImportDialog(self)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                # 刷新统计
                stats = self._question_service.get_statistics()
                self._stats_label.setText(
                    f"题目总数: {stats.get('total', 0)} | "
                    f"分类数: {stats.get('category_count', 0)}"
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "导入失败",
                f"从粉笔网导入失败: {str(e)}"
            )
            logger.error(f"粉笔导入失败: {e}")

    def _on_export(self) -> None:
        """导出题库"""
        try:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "保存题库文件",
                "questions.json",
                JSON_SAVE_FILTER
            )
            if not file_path:
                return
            self._question_service.export_to_json(file_path)
            QtWidgets.QMessageBox.information(
                self,
                "导出成功",
                f"题库已导出到: {file_path}"
            )
            logger.info(f"导出题库: {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "导出失败",
                f"导出题库失败: {str(e)}"
            )
            logger.error(f"导出题库失败: {e}")

    def _on_clear(self) -> None:
        """清空题库"""
        reply = QtWidgets.QMessageBox.warning(
            self,
            "确认清空",
            "确定要清空所有题目吗？此操作不可恢复！",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            count = self._question_service.clear_all()
            QtWidgets.QMessageBox.information(
                self,
                "清空成功",
                f"已清空 {count} 道题目"
            )
            stats = self._question_service.get_statistics()
            self._stats_label.setText(
                f"题目总数: {stats.get('total', 0)} | "
                f"分类数: {stats.get('category_count', 0)}"
            )
            logger.info(f"清空题库: 删除{count}题")
