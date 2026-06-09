"""
DeskStudy 主应用
整合所有组件
"""

import sys
import ctypes
from pathlib import Path
from typing import Optional

from PySide6 import QtWidgets, QtCore, QtGui

from app.DeskStudy.config.settings import get_settings
from app.DeskStudy.database.connection import init_database
from app.DeskStudy.services.question_service import QuestionService
from app.DeskStudy.services.wrong_question_service import WrongQuestionService
from app.DeskStudy.services.review_service import ReviewService
from app.DeskStudy.services.statistics_service import StatisticsService
from app.DeskStudy.ui.floating_ball import FloatingBall
from app.DeskStudy.ui.question_card import QuestionCard
from app.DeskStudy.ui.system_tray import SystemTrayManager
from app.DeskStudy.ui.settings_dialog import SettingsDialog
from app.DeskStudy.ui.license_dialog import LicenseDialog
from app.DeskStudy.ui.wrong_question_dialog import WrongQuestionDialog
from app.DeskStudy.ui.statistics_dialog import StatisticsDialog
from app.DeskStudy.core.license import LicenseManager
from app.DeskStudy.utils.logger import setup_logger, get_logger
from app.DeskStudy.utils.hotkey import get_hotkey_manager
from app.DeskStudy.utils.resource_path import get_resource_path

logger = get_logger(__name__)


class QuestionPanel(QtWidgets.QFrame):
    """题目面板窗口"""

    clicked_outside = QtCore.Signal()  # 点击外部信号

    def __init__(self, question_card: 'QuestionCard', parent=None):
        super().__init__(parent)
        self._question_card = question_card
        self._is_dragging = False
        self._drag_start_pos = None
        self._panel_start_pos = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._question_card)

        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖动"""
        if event.button() == QtCore.Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._panel_start_pos = self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖动窗口"""
        if self._is_dragging and self._drag_start_pos and self._panel_start_pos:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._panel_start_pos + delta
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 结束拖动"""
        if event.button() == QtCore.Qt.LeftButton:
            self._is_dragging = False
            event.accept()

    def adapt_size(self) -> None:
        """根据内容自适应调整面板大小"""
        card_h = self._question_card.height()
        self.setFixedSize(self._question_card.size())

    def is_inside(self, global_pos: QtCore.QPoint) -> bool:
        """检查全局坐标是否在面板内"""
        return self.rect().contains(self.mapFromGlobal(global_pos))

    def show_at(self, x: int, y: int) -> None:
        """在指定位置显示"""
        from app.DeskStudy.ui.question_card import PANEL_WIDTH
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geom = screen.geometry()

        if x < screen_geom.width() // 2:
            show_x = x + 70
        else:
            show_x = x - PANEL_WIDTH - 10

        panel_height = self.height()
        show_y = max(0, min(y, screen_geom.height() - panel_height))

        self.move(show_x, show_y)
        self.show()


class BossKeySignal(QtCore.QObject):
    """老板键信号，用于跨线程调用"""
    triggered = QtCore.Signal()

    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self._callback = callback
        self.triggered.connect(self._on_triggered)

    def _on_triggered(self) -> None:
        logger.info("BossKeySignal: 信号已到达主线程，执行回调")
        self._callback()

    def emit_from_thread(self) -> None:
        logger.info("BossKeySignal: 从后台线程发射信号")
        self.triggered.emit()


class DeskStudyApp(QtCore.QObject):
    """DeskStudy 主应用类"""

    def __init__(self):
        super().__init__()  # 初始化 QObject
        setup_logger(log_level="INFO")
        logger.info("=" * 50)
        logger.info("DeskStudy 启动中...")
        logger.info("=" * 50)

        self._app: Optional[QtWidgets.QApplication] = None
        self._main_window: Optional[QtWidgets.QMainWindow] = None
        self._floating_ball: Optional[FloatingBall] = None
        self._question_panel: Optional[QuestionPanel] = None
        self._question_card: Optional[QuestionCard] = None
        self._system_tray: Optional[SystemTrayManager] = None
        self._settings_dialog: Optional[SettingsDialog] = None
        self._wrong_question_dialog: Optional[WrongQuestionDialog] = None
        self._stats_dialog: Optional[StatisticsDialog] = None

        self._is_hidden = False
        self._is_review_mode = False  # False=刷题模式, True=复盘模式
        self._study_timer: Optional[QtCore.QTimer] = None
        self._study_start_time: Optional[QtCore.QDateTime] = None

        self._question_service: Optional[QuestionService] = None
        self._wrong_service: Optional[WrongQuestionService] = None
        self._review_service: Optional[ReviewService] = None
        self._stats_service: Optional[StatisticsService] = None
        self._license_manager: Optional[LicenseManager] = None

    def initialize(self) -> bool:
        """初始化应用"""
        try:
            logger.info("检查许可证...")
            self._license_manager = LicenseManager()
            if not self._license_manager.is_licensed:
                logger.warning("许可证未激活或已过期")
                dialog = LicenseDialog(self._license_manager)
                if dialog.exec() != QtWidgets.QDialog.Accepted or not self._license_manager.is_licensed:
                    logger.info("用户未激活许可证，退出应用")
                    return False
                logger.info("许可证激活成功")
            else:
                status = self._license_manager.check()
                logger.info(f"许可证有效: {status['type_name']}, 剩余 {status['remaining_days']} 天")

            logger.info("初始化数据库...")
            init_database()

            logger.info("初始化服务...")
            self._question_service = QuestionService()
            self._wrong_service = WrongQuestionService()
            self._review_service = ReviewService()
            self._stats_service = StatisticsService()

            logger.info("检查示例题库...")
            self._check_sample_questions()

            logger.info("初始化主窗口...")
            self._init_main_window()

            logger.info("初始化题目卡片...")
            self._init_question_card()

            logger.info("初始化悬浮球...")
            self._init_floating_ball()

            logger.info("初始化系统托盘...")
            self._init_system_tray()

            logger.info("初始化热键...")
            self._init_hotkeys()

            self._setup_fullscreen_detection()

            logger.info("DeskStudy 初始化完成!")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _check_sample_questions(self) -> None:
        """检查并导入示例题目"""
        try:
            if len(self._question_service.get_all_questions()) == 0:
                # 使用资源路径工具，兼容开发环境和打包后环境
                sample_file = get_resource_path("sample_questions.json")
                if sample_file.exists():
                    imported = self._question_service.import_from_json(str(sample_file))
                    logger.info(f"已自动导入 {imported} 道示例题目")
                else:
                    logger.warning(f"示例题库文件不存在: {sample_file}")
        except Exception as e:
            logger.error(f"检查示例题目失败: {e}")

    def _init_main_window(self) -> None:
        """初始化主窗口"""
        self._main_window = QtWidgets.QMainWindow()
        self._main_window.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self._main_window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._main_window.setFixedSize(1, 1)
        self._main_window.move(-1000, -1000)
        self._main_window.show()

    def _init_question_card(self) -> None:
        """初始化题目卡片"""
        self._question_card = QuestionCard(
            question_service=self._question_service,
            wrong_service=self._wrong_service,
            review_service=self._review_service,
            stats_service=self._stats_service
        )
        self._question_card.size_changed.connect(self._on_card_size_changed)

    def _init_floating_ball(self) -> None:
        """初始化悬浮球"""
        self._question_panel = QuestionPanel(self._question_card)
        self._floating_ball = FloatingBall(
            on_ball_clicked=self._on_ball_clicked
        )
        self._floating_ball.show()

        # 定时器检测全局鼠标点击
        self._click_check_timer = QtCore.QTimer(self)
        self._click_check_timer.timeout.connect(self._check_mouse_click)
        self._click_check_timer.start(50)  # 每50ms检测一次
        self._last_mouse_pressed = False

    def _check_mouse_click(self) -> None:
        """检测全局鼠标点击"""
        if not self._question_panel or not self._question_panel.isVisible():
            return

        # 使用 Windows API 检测全局鼠标左键状态
        VK_LBUTTON = 0x01
        mouse_pressed = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000

        # 检测从按下到释放的状态变化
        if self._last_mouse_pressed and not mouse_pressed:
            # 鼠标释放时检查位置
            cursor_pos = QtGui.QCursor.pos()

            # 检查是否点击在悬浮球上
            ball_rect = self._floating_ball.geometry()
            # 检查是否点击在题目面板上
            panel_inside = self._question_panel.is_inside(cursor_pos)
            ball_inside = ball_rect.contains(cursor_pos)

            # logger.info(f"鼠标点击检测: pos={cursor_pos}, panel_inside={panel_inside}, ball_inside={ball_inside}")

            if not panel_inside and not ball_inside:
                logger.info(f"点击外部，隐藏面板")
                self._question_panel.hide()

        self._last_mouse_pressed = bool(mouse_pressed)

    def _on_ball_clicked(self) -> None:
        """悬浮球被点击"""
        if self._question_panel and self._question_panel.isVisible():
            self._question_panel.hide()
        elif self._floating_ball and self._question_panel:
            pos = self._floating_ball.pos()
            # 设置卡片模式
            self._question_card.set_review_mode(self._is_review_mode)
            self._question_panel.show_at(pos.x(), pos.y())
            # 只在题目为空时才加载新题
            if not self._question_card._current_question:
                self._question_card.refresh()

    def _on_card_size_changed(self) -> None:
        """题目卡片大小变化时调整面板"""
        if self._question_panel:
            self._question_panel.adapt_size()

    def _init_system_tray(self) -> None:
        """初始化系统托盘"""
        self._system_tray = SystemTrayManager(
            on_practice_mode=self._on_practice_mode,
            on_review_mode=self._on_review_mode,
            on_show_statistics=self._on_show_statistics,
            on_open_settings=self._on_open_settings,
            on_exit=self._on_exit,
            on_open_license=self._on_open_license,
            on_open_wrong_questions=self._on_open_wrong_questions,
            on_donate=self._on_donate
        )

    def _init_hotkeys(self) -> None:
        """初始化热键"""
        hotkey_manager = get_hotkey_manager()
        settings = get_settings()

        hotkey_manager.register(
            settings.hotkey.boss_key,
            self._boss_key_signal.emit_from_thread
        )

        hotkey_manager.start()
        logger.info(f"老板键已注册: {settings.hotkey.boss_key}")

    def _setup_fullscreen_detection(self) -> None:
        """设置全屏检测"""
        self._fullscreen_watcher = QtCore.QTimer()
        self._fullscreen_watcher.timeout.connect(self._check_fullscreen)
        self._fullscreen_watcher.start(1000)

    def _check_fullscreen(self) -> None:
        """检测全屏应用"""
        settings = get_settings()
        if not settings.fullscreen_pause:
            return

        screen = self._app.primaryScreen()
        if not screen:
            return

        for window in self._app.topLevelWindows():
            if window.isVisible():
                geo = window.geometry()
                if (geo.width() >= screen.geometry().width() and
                    geo.height() >= screen.geometry().height()):
                    if not self._is_hidden:
                        self._on_boss_key()  # 触发老板键隐藏
                        logger.debug("检测到全屏应用，自动隐藏")
                    return

    def _on_boss_key(self) -> None:
        """老板键响应"""
        logger.info(f"老板键触发! is_hidden={self._is_hidden}")
        if self._is_hidden:
            self._show_all()
        else:
            self._hide_all()
        self._is_hidden = not self._is_hidden
        logger.info(f"老板键处理完成, is_hidden={self._is_hidden}")

    def _hide_all(self) -> None:
        """隐藏所有窗口"""
        logger.info("执行隐藏所有窗口...")
        if self._floating_ball:
            logger.info(f"隐藏悬浮球, 当前visible={self._floating_ball.isVisible()}")
            self._floating_ball.hide_all()
        if self._question_panel:
            logger.info(f"隐藏题目面板, 当前visible={self._question_panel.isVisible()}")
            self._question_panel.hide()
        if self._main_window:
            self._main_window.hide()
        logger.debug("已隐藏所有窗口")

    def _show_all(self) -> None:
        """显示所有窗口"""
        logger.info("执行显示所有窗口...")
        if self._floating_ball:
            self._floating_ball.show_all()
            logger.info(f"显示悬浮球, 当前visible={self._floating_ball.isVisible()}")
        if self._main_window:
            self._main_window.show()
        logger.debug("已显示所有窗口")

    def _on_practice_mode(self) -> None:
        """切换到刷题模式"""
        self._is_review_mode = False
        if self._system_tray:
            self._system_tray.set_mode(False)
        logger.info("切换到刷题模式")

    def _on_review_mode(self) -> None:
        """切换到复盘模式"""
        self._is_review_mode = True
        if self._system_tray:
            self._system_tray.set_mode(True)
        logger.info("切换到复盘模式")

    def _start_study_timer(self) -> None:
        """启动学习计时器"""
        self._study_start_time = QtCore.QDateTime.currentDateTime()

        if self._study_timer:
            self._study_timer.stop()

        self._study_timer = QtCore.QTimer()
        self._study_timer.timeout.connect(self._update_study_duration)
        self._study_timer.start(60000)

    def _stop_study_timer(self) -> None:
        """停止学习计时器"""
        if self._study_timer:
            self._study_timer.stop()
            self._study_timer = None

        if self._study_start_time:
            duration = self._study_start_time.secsTo(QtCore.QDateTime.currentDateTime())
            if duration > 0:
                self._stats_service.record_study_duration(duration)
            self._study_start_time = None

    def _update_study_duration(self) -> None:
        """更新学习时长"""
        if self._study_start_time:
            self._stats_service.record_study_duration(60)

    def _on_show_statistics(self) -> None:
        """显示统计"""
        if self._stats_dialog is None:
            self._stats_dialog = StatisticsDialog()
        self._stats_dialog.exec()

    def _on_open_settings(self) -> None:
        """打开设置"""
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog()

        result = self._settings_dialog.exec()

        if result == QtWidgets.QDialog.Accepted:
            if self._floating_ball:
                self._floating_ball.refresh_from_settings()

    def _on_open_license(self) -> None:
        """打开许可证"""
        if self._license_manager:
            dialog = LicenseDialog(self._license_manager)
            dialog.exec()

    def _on_open_wrong_questions(self) -> None:
        """打开错题本"""
        if self._wrong_question_dialog is None:
            self._wrong_question_dialog = WrongQuestionDialog()
        self._wrong_question_dialog.exec()

    def _on_donate(self) -> None:
        """打开赞赏对话框"""
        from app.DeskStudy.ui.donate_dialog import DonateDialog
        dialog = DonateDialog()
        dialog.exec()

    def _on_exit(self) -> None:
        """退出应用"""
        logger.info("DeskStudy 退出中...")

        self._stop_study_timer()

        if self._floating_ball:
            self._floating_ball.hide_all()
        if self._question_panel:
            self._question_panel.hide()

        if self._system_tray:
            self._system_tray.dispose()

        hotkey_manager = get_hotkey_manager()
        hotkey_manager.stop()

        if self._app:
            self._app.quit()

    def run(self) -> None:
        """运行应用"""
        self._app = QtWidgets.QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)

        self._app.setApplicationName("DeskStudy")
        self._app.setApplicationVersion("1.0.0")

        self._boss_key_signal = BossKeySignal(self._on_boss_key)
        logger.info("BossKeySignal 已创建并连接")

        if not self.initialize():
            QtWidgets.QMessageBox.critical(
                None,
                "初始化错误",
                "DeskStudy初始化失败，请检查日志！"
            )
            sys.exit(1)

        sys.exit(self._app.exec())


def main():
    """主入口"""
    app = DeskStudyApp()
    app.run()


if __name__ == "__main__":
    main()
