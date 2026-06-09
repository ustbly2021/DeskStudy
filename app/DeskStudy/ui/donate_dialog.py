"""
赞赏作者对话框
"""

import sys
import os
from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional

from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class DonateDialog(QtWidgets.QDialog):
    """赞赏作者对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("赞赏作者")
        self.setFixedSize(500, 400)
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
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title = QtWidgets.QLabel("感谢您的支持！")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #6366F1;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # 描述
        desc = QtWidgets.QLabel(
            "如果您觉得这个软件对您有帮助，\n"
            "欢迎扫码赞赏支持作者继续开发 ❤️"
        )
        desc.setStyleSheet("font-size: 14px; color: #9CA3AF;")
        desc.setAlignment(QtCore.Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 二维码区域
        qr_layout = QtWidgets.QHBoxLayout()
        qr_layout.setSpacing(40)

        # 微信二维码
        wechat_widget = self._create_qr_widget(
            "微信赞赏",
            self._get_qr_path("wechat_qr.png"),
            "#07C160"
        )
        qr_layout.addWidget(wechat_widget)

        # 支付宝二维码
        alipay_widget = self._create_qr_widget(
            "支付宝赞赏",
            self._get_qr_path("alipay_qr.png"),
            "#1677FF"
        )
        qr_layout.addWidget(alipay_widget)

        layout.addLayout(qr_layout)
        layout.addStretch()

        # 提示
        # hint = QtWidgets.QLabel("长按识别二维码或保存图片后扫码")
        # hint.setStyleSheet("font-size: 12px; color: #6B7280;")
        # hint.setAlignment(QtCore.Qt.AlignCenter)
        # layout.addWidget(hint)

    def _get_qr_path(self, filename: str) -> Optional[str]:
        """获取二维码图片路径"""
        # donate_dialog.py 在 app/DeskStudy/ui/ 目录下
        # assets 在 DeskStudy/assets/ 目录下
        # 需要往上走3层: ui -> DeskStudy -> app -> DeskStudy (根目录)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        possible_paths = [
            # 开发环境: 从 ui 目录往上走3层到项目根目录
            os.path.join(current_dir, "..", "..", "..", "assets", filename),
            # 打包后的环境: assets 在 _internal/assets 或直接在 assets
            os.path.join(current_dir, "assets", filename),
        ]

        # PyInstaller 打包后的路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            possible_paths.insert(0, os.path.join(base_path, "assets", filename))

        for path in possible_paths:
            abs_path = os.path.abspath(path)
            logger.debug(f"检查路径: {abs_path}")
            if os.path.exists(abs_path):
                logger.info(f"找到二维码图片: {abs_path}")
                return abs_path

        logger.warning(f"未找到二维码图片: {filename}，已检查路径: {possible_paths}")
        return None

    def _create_qr_widget(self, title: str, qr_path: Optional[str], color: str) -> QtWidgets.QWidget:
        """创建二维码展示组件"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # 二维码图片
        qr_label = QtWidgets.QLabel()
        qr_label.setFixedSize(180, 180)
        qr_label.setStyleSheet(f"""
            QLabel {{
                background: white;
                border: 3px solid {color};
                border-radius: 10px;
            }}
        """)
        qr_label.setAlignment(QtCore.Qt.AlignCenter)

        if qr_path and os.path.exists(qr_path):
            pixmap = QtGui.QPixmap(qr_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    170, 170,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
                qr_label.setPixmap(scaled)
            else:
                qr_label.setText("图片加载失败")
                qr_label.setStyleSheet(f"""
                    QLabel {{
                        background: white;
                        border: 3px solid {color};
                        border-radius: 10px;
                        color: #666;
                        font-size: 12px;
                    }}
                """)
        else:
            qr_label.setText("请添加二维码图片")
            qr_label.setStyleSheet(f"""
                QLabel {{
                    background: white;
                    border: 3px solid {color};
                    border-radius: 10px;
                    color: #666;
                    font-size: 12px;
                }}
            """)

        layout.addWidget(qr_label)

        # 标题
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        return widget

