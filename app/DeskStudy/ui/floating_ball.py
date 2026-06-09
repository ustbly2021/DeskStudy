"""
悬浮球窗口实现
"""

from typing import Optional, Callable

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QGraphicsOpacityEffect

from app.DeskStudy.config.settings import get_settings
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class FloatingBall(QtWidgets.QWidget):
    """桌面悬浮球窗口"""

    def __init__(
        self,
        on_ball_clicked: Optional[Callable[[], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.on_ball_clicked = on_ball_clicked

        self._settings = get_settings()
        self.BALL_SIZE = self._settings.floating_ball.size  # 从设置读取大小
        self._is_dragging = False
        self._drag_start_pos = None
        self._ball_start_pos = None
        self._snap_anim = None
        self._opacity_effect = None

        self._setup_window()
        self._create_ui()

        logger.info("悬浮球初始化完成")

    def _setup_window(self) -> None:
        """设置窗口属性"""
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            x = screen_geom.right() - self.BALL_SIZE - 50
            y = screen_geom.height() // 2
            self.move(int(x), int(y))

        self.setFixedSize(self.BALL_SIZE, self.BALL_SIZE)

    def _create_ui(self) -> None:
        """创建UI"""
        self._ball = QtWidgets.QFrame(self)
        self._ball.setFixedSize(self.BALL_SIZE, self.BALL_SIZE)
        self._ball.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.5,
                    stop: 0 #6366F1,
                    stop: 1 #4F46E5
                );
                border-radius: {self.BALL_SIZE // 2}px;
                border: none;
            }}
        """)

        self._icon = QtWidgets.QLabel("📚", self._ball)
        self._icon.setAlignment(QtCore.Qt.AlignCenter)
        self._icon.setStyleSheet("background: transparent; border: none;")
        self._icon.setFixedSize(self.BALL_SIZE, self.BALL_SIZE)
        font = self._icon.font()
        font.setPointSize(self.BALL_SIZE // 3)
        self._icon.setFont(font)

        self._opacity_effect = QGraphicsOpacityEffect(self._ball)
        self._opacity_effect.setOpacity(self._settings.floating_ball.opacity)
        self._ball.setGraphicsEffect(self._opacity_effect)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """鼠标按下"""
        if event.button() == QtCore.Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._ball_start_pos = self.pos()
            self._start_drag_pos = self.pos()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """鼠标移动"""
        if self._is_dragging and self._drag_start_pos and self._ball_start_pos:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._ball_start_pos + delta
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """鼠标释放"""
        if event.button() == QtCore.Qt.LeftButton:
            was_dragged = self._is_dragging
            self._is_dragging = False

            if not was_dragged or (self._start_drag_pos and self.pos() == self._start_drag_pos):
                if self.on_ball_clicked:
                    self.on_ball_clicked()

            if self._settings.floating_ball.edge_snap_enabled:
                self._snap_to_edge()

            event.accept()

    def _snap_to_edge(self) -> None:
        """吸附到屏幕边缘"""
        pos = self.pos()
        screen = QtWidgets.QApplication.primaryScreen()
        if not screen:
            return
        screen_geom = screen.geometry()
        half_screen = screen_geom.width() // 2

        if pos.x() + self.width() // 2 < half_screen:
            new_x = 0
        else:
            new_x = screen_geom.width() - self.width()

        new_y = max(0, min(pos.y(), screen_geom.height() - self.height()))

        if new_x == pos.x() and new_y == pos.y():
            return

        if self._snap_anim is not None:
            self._snap_anim.stop()

        self._snap_anim = QtCore.QPropertyAnimation(self, b"pos")
        self._snap_anim.setDuration(200)
        self._snap_anim.setStartValue(pos)
        self._snap_anim.setEndValue(QtCore.QPoint(new_x, new_y))
        self._snap_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._snap_anim.start()

    def set_opacity(self, opacity: float) -> None:
        """设置透明度"""
        if self._opacity_effect:
            self._opacity_effect.setOpacity(max(0.1, min(1.0, opacity)))

    def set_size(self, size: int) -> None:
        """设置悬浮球大小"""
        self.BALL_SIZE = size
        self.setFixedSize(size, size)
        self._ball.setFixedSize(size, size)
        self._ball.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.5,
                    stop: 0 #6366F1,
                    stop: 1 #4F46E5
                );
                border-radius: {size // 2}px;
                border: none;
            }}
        """)
        self._icon.setFixedSize(size, size)
        font_size = max(12, size // 3)
        self._icon.setStyleSheet(f"background: transparent; border: none; font-size: {font_size}px;")

    def refresh_from_settings(self) -> None:
        """从设置刷新悬浮球"""
        self._settings = get_settings()
        self.set_opacity(self._settings.floating_ball.opacity)
        self.set_size(self._settings.floating_ball.size)

    def hide_all(self) -> None:
        """隐藏所有"""
        self.hide()

    def show_all(self) -> None:
        """显示所有"""
        self.show()
