"""
系统托盘管理
"""

from typing import Optional, Callable

from PySide6 import QtWidgets, QtCore, QtGui

from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class SystemTrayManager:
    """系统托盘管理器"""

    def __init__(
        self,
        on_practice_mode: Optional[Callable] = None,
        on_review_mode: Optional[Callable] = None,
        on_show_statistics: Optional[Callable] = None,
        on_open_settings: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        on_open_license: Optional[Callable] = None,
        on_open_wrong_questions: Optional[Callable] = None,
        on_donate: Optional[Callable] = None
    ):
        self._on_practice_mode = on_practice_mode
        self._on_review_mode = on_review_mode
        self._on_show_statistics = on_show_statistics
        self._on_open_settings = on_open_settings
        self._on_exit = on_exit
        self._on_open_license = on_open_license
        self._on_open_wrong_questions = on_open_wrong_questions
        self._on_donate = on_donate

        self._is_review_mode = False  # False=刷题模式, True=复盘模式

        self._tray_icon: Optional[QtWidgets.QSystemTrayIcon] = None
        self._tray_menu: Optional[QtWidgets.QMenu] = None

        self._setup_tray()

        logger.info("系统托盘初始化完成")

    def _setup_tray(self) -> None:
        """设置系统托盘"""
        self._tray_icon = QtWidgets.QSystemTrayIcon()

        self._tray_icon.setToolTip("DeskStudy - 桌面学习助手")

        icon = self._create_icon()
        self._tray_icon.setIcon(icon)

        self._tray_menu = QtWidgets.QMenu()

        self._practice_action = self._tray_menu.addAction("📝 刷题模式")
        self._practice_action.triggered.connect(self._on_practice_mode_clicked)

        self._review_action = self._tray_menu.addAction("🔄 复盘模式")
        self._review_action.triggered.connect(self._on_review_mode_clicked)

        self._tray_menu.addSeparator()

        self._stats_action = self._tray_menu.addAction("📊 今日统计")
        self._stats_action.triggered.connect(self._on_show_statistics)

        self._wrong_action = self._tray_menu.addAction("📚 错题本")
        self._wrong_action.triggered.connect(self._on_open_wrong_questions)

        self._settings_action = self._tray_menu.addAction("⚙ 设置")
        self._settings_action.triggered.connect(self._on_open_settings)

        self._license_action = self._tray_menu.addAction("🔑 许可证")
        self._license_action.triggered.connect(self._on_open_license_clicked)

        self._donate_action = self._tray_menu.addAction("❤️ 赞赏作者")
        self._donate_action.triggered.connect(self._on_donate_clicked)

        self._tray_menu.addSeparator()

        self._exit_action = self._tray_menu.addAction("❌ 退出")
        self._exit_action.triggered.connect(self._on_exit)

        self._tray_icon.setContextMenu(self._tray_menu)

        self._tray_icon.activated.connect(self._on_tray_activated)

        self._tray_icon.show()

    def _create_icon(self) -> QtGui.QIcon:
        """创建图标"""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        gradient = QtGui.QRadialGradient(16, 16, 14)
        gradient.setColorAt(0, QtGui.QColor("#6366F1"))
        gradient.setColorAt(1, QtGui.QColor("#4F46E5"))

        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)

        painter.setPen(QtGui.QColor("white"))
        painter.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, "D")

        painter.end()

        return QtGui.QIcon(pixmap)

    def _on_tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        """托盘图标激活处理"""
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            if self._on_practice_mode:
                self._on_practice_mode()

    def _on_practice_mode_clicked(self) -> None:
        """切换到刷题模式"""
        self._is_review_mode = False
        self._update_menu_state()
        if self._on_practice_mode:
            self._on_practice_mode()
        logger.info("切换到刷题模式")

    def _on_review_mode_clicked(self) -> None:
        """切换到复盘模式"""
        self._is_review_mode = True
        self._update_menu_state()
        if self._on_review_mode:
            self._on_review_mode()
        logger.info("切换到复盘模式")

    def _on_show_statistics(self) -> None:
        """显示统计"""
        if self._on_show_statistics:
            self._on_show_statistics()

    def _on_open_settings(self) -> None:
        """打开设置"""
        if self._on_open_settings:
            self._on_open_settings()

    def _on_open_license_clicked(self) -> None:
        """打开许可证"""
        if self._on_open_license:
            self._on_open_license()

    def _on_open_wrong_questions(self) -> None:
        """打开错题本"""
        if self._on_open_wrong_questions:
            self._on_open_wrong_questions()

    def _on_donate_clicked(self) -> None:
        """赞赏作者"""
        if self._on_donate:
            self._on_donate()

    def _on_exit(self) -> None:
        """退出应用"""
        if self._on_exit:
            self._on_exit()

    def _update_menu_state(self) -> None:
        """更新菜单状态"""
        if self._is_review_mode:
            self._practice_action.setEnabled(True)
            self._review_action.setEnabled(False)
        else:
            self._practice_action.setEnabled(False)
            self._review_action.setEnabled(True)

    def set_mode(self, is_review: bool) -> None:
        """设置模式"""
        self._is_review_mode = is_review
        self._update_menu_state()

    def show_notification(self, title: str, message: str) -> None:
        """显示通知"""
        if self._tray_icon:
            self._tray_icon.showMessage(title, message, QtWidgets.QSystemTrayIcon.Information, 3000)

    def hide(self) -> None:
        """隐藏托盘图标"""
        if self._tray_icon:
            self._tray_icon.hide()

    def show(self) -> None:
        """显示托盘图标"""
        if self._tray_icon:
            self._tray_icon.show()

    def setToolTip(self, tooltip: str) -> None:
        """设置提示文本"""
        if self._tray_icon:
            self._tray_icon.setToolTip(tooltip)

    def dispose(self) -> None:
        """释放资源"""
        if self._tray_icon:
            self._tray_icon.hide()
            self._tray_icon.deleteLater()
            self._tray_icon = None
        logger.info("系统托盘已销毁")
