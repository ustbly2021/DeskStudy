"""
许可证激活对话框
支持在线激活和离线激活两种方式
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from app.DeskStudy.core.license import LicenseManager, LICENSE_TYPES
from app.DeskStudy.core.online_activation import OnlineActivationService
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class LicenseDialog(QtWidgets.QDialog):
    """许可证激活对话框"""

    def __init__(self, license_manager: LicenseManager, parent=None):
        super().__init__(parent)
        self._license_manager = license_manager
        self._activation_service = OnlineActivationService()
        self._activated = False
        self._setup_ui()

    @property
    def activated(self) -> bool:
        return self._activated

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("DeskStudy - 许可证激活")
        self.setFixedSize(520, 520)
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
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                background: transparent;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: #9CA3AF;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: rgba(99, 102, 241, 0.2);
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.1);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("🔑 DeskStudy 许可证激活")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #6366F1;")
        layout.addWidget(title, alignment=QtCore.Qt.AlignCenter)

        # 状态显示
        status = self._license_manager.check()
        if status["licensed"]:
            info_text = (
                f"✅ 已激活: {status['type_name']}\n"
                f"📅 剩余: {status['remaining_days']} 天 | 到期: {status['expires_at']}"
            )
            info_color = "#10B981"
        else:
            info_text = "❌ 未激活 - 请选择激活方式"
            info_color = "#EF4444"

        self._status_label = QtWidgets.QLabel(info_text)
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet(f"color: {info_color}; font-size: 13px; padding: 8px 0;")
        layout.addWidget(self._status_label)

        # Tab 切换
        self._tab_widget = QtWidgets.QTabWidget()

        # 在线激活 Tab
        online_widget = self._create_online_tab()
        self._tab_widget.addTab(online_widget, "🌐 在线激活")

        # 离线激活 Tab
        offline_widget = self._create_offline_tab()
        self._tab_widget.addTab(offline_widget, "📋 离线激活")

        layout.addWidget(self._tab_widget)

        # 消息提示
        self._message_label = QtWidgets.QLabel("")
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._message_label)

        # 底部按钮
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        if status["licensed"]:
            deactivate_btn = QtWidgets.QPushButton("注销许可证")
            deactivate_btn.setFixedSize(100, 36)
            deactivate_btn.setCursor(QtCore.Qt.PointingHandCursor)
            deactivate_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(239, 68, 68, 0.2);
                    color: #EF4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.3);
                }
            """)
            deactivate_btn.clicked.connect(self._on_deactivate)
            btn_layout.addWidget(deactivate_btn)

        self._close_btn = QtWidgets.QPushButton("关闭")
        self._close_btn.setFixedSize(100, 36)
        self._close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: #6366F1;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #5558E3;
            }
        """)
        self._close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

        # 授权类型提示
        tip = QtWidgets.QLabel(
            "授权类型: 试用版(1天) | 月卡(30天) | 半年卡(180天) | 年卡(365天)"
        )
        tip.setStyleSheet("color: #4B5563; font-size: 10px;")
        layout.addWidget(tip, alignment= QtCore.Qt.AlignCenter)

    def _create_online_tab(self) -> QtWidgets.QWidget:
        """创建在线激活Tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(12)

        # 说明
        desc = QtWidgets.QLabel("输入购买获得的激活码，系统将自动完成激活")
        desc.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(desc)

        # 激活码输入
        code_label = QtWidgets.QLabel("激活码:")
        code_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(code_label)

        self._activation_code_input = QtWidgets.QLineEdit()
        self._activation_code_input.setPlaceholderText("请输入激活码，如: XXXX-XXXX-XXXX-XXXX")
        self._activation_code_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366F1;
            }
        """)
        layout.addWidget(self._activation_code_input)

        # 机器码显示
        mid_label = QtWidgets.QLabel("机器码 (自动获取):")
        mid_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(mid_label)

        self._machine_id_display = QtWidgets.QLabel(
            self._activation_service.get_machine_id_display()
        )
        self._machine_id_display.setStyleSheet(
            "color: #6366F1; font-size: 12px; font-family: Consolas, monospace; "
            "background: rgba(99, 102, 241, 0.1); padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(self._machine_id_display)

        # 激活按钮
        self._online_activate_btn = QtWidgets.QPushButton("🚀 立即激活")
        self._online_activate_btn.setFixedHeight(40)
        self._online_activate_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._online_activate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:1 #8B5CF6);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5558E3, stop:1 #7C3AED);
            }
            QPushButton:pressed {
                background: #4F46E5;
            }
        """)
        self._online_activate_btn.clicked.connect(self._on_online_activate)
        layout.addWidget(self._online_activate_btn)

        layout.addStretch()
        return widget

    def _create_offline_tab(self) -> QtWidgets.QWidget:
        """创建离线激活Tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(12)

        # 说明
        desc = QtWidgets.QLabel("将机器码发送给客服，获取许可证密钥后粘贴到下方")
        desc.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(desc)

        # 机器码
        mid_label = QtWidgets.QLabel("机器码:")
        mid_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(mid_label)

        mid_layout = QtWidgets.QHBoxLayout()
        self._offline_machine_id = QtWidgets.QLabel(self._license_manager.machine_id)
        self._offline_machine_id.setStyleSheet(
            "color: #9CA3AF; font-size: 11px; font-family: Consolas, monospace; "
            "background: rgba(255,255,255,0.05); padding: 8px; border-radius: 4px;"
        )
        self._offline_machine_id.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        mid_layout.addWidget(self._offline_machine_id, 1)

        copy_btn = QtWidgets.QPushButton("复制")
        copy_btn.setFixedSize(60, 28)
        copy_btn.setCursor(QtCore.Qt.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        copy_btn.clicked.connect(self._copy_machine_id)
        mid_layout.addWidget(copy_btn)
        layout.addLayout(mid_layout)

        # 许可证密钥输入
        key_label = QtWidgets.QLabel("许可证密钥:")
        key_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(key_label)

        self._key_input = QtWidgets.QTextEdit()
        self._key_input.setFixedHeight(80)
        self._key_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.08);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-family: Consolas, monospace;
            }
            QTextEdit:focus {
                border-color: #6366F1;
            }
        """)
        self._key_input.setPlaceholderText("请粘贴许可证密钥...")
        layout.addWidget(self._key_input)

        # 激活按钮
        self._offline_activate_btn = QtWidgets.QPushButton("🔑 离线激活")
        self._offline_activate_btn.setFixedHeight(40)
        self._offline_activate_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._offline_activate_btn.setStyleSheet("""
            QPushButton {
                background: rgba(99, 102, 241, 0.2);
                color: #6366F1;
                border: 1px solid #6366F1;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.3);
            }
        """)
        self._offline_activate_btn.clicked.connect(self._on_offline_activate)
        layout.addWidget(self._offline_activate_btn)

        layout.addStretch()
        return widget

    def _copy_machine_id(self) -> None:
        """复制机器码"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self._license_manager.machine_id)
        self._show_message("✅ 机器码已复制到剪贴板", "#10B981")

    def _show_message(self, text: str, color: str = "#9CA3AF") -> None:
        """显示消息"""
        self._message_label.setText(text)
        self._message_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def _on_online_activate(self) -> None:
        """在线激活"""
        code = self._activation_code_input.text().strip()
        if not code:
            self._show_message("❌ 请输入激活码", "#EF4444")
            return

        self._show_message("⏳ 正在激活...", "#6366F1")
        self._online_activate_btn.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        # 调用在线激活服务
        result = self._activation_service.activate(code)

        self._online_activate_btn.setEnabled(True)

        if result.get("success"):
            # 使用返回的许可证密钥激活
            license_key = result.get("license_key")
            if license_key:
                activate_result = self._license_manager.activate(license_key)
                if activate_result["success"]:
                    self._show_message(f"✅ {result.get('message', '激活成功')}", "#10B981")
                    self._activated = True
                    QtCore.QTimer.singleShot(1500, self.accept)
                else:
                    self._show_message(f"❌ {activate_result['message']}", "#EF4444")
            else:
                self._show_message(f"✅ {result.get('message', '激活成功')}", "#10B981")
                self._activated = True
                QtCore.QTimer.singleShot(1500, self.accept)
        else:
            self._show_message(f"❌ {result.get('message', '激活失败')}", "#EF4444")

    def _on_offline_activate(self) -> None:
        """离线激活"""
        key = self._key_input.toPlainText().strip()
        if not key:
            self._show_message("❌ 请输入许可证密钥", "#EF4444")
            return

        result = self._license_manager.activate(key)
        if result["success"]:
            self._show_message(f"✅ {result['message']}", "#10B981")
            self._activated = True
            QtCore.QTimer.singleShot(1500, self.accept)
        else:
            self._show_message(f"❌ {result['message']}", "#EF4444")

    def _on_deactivate(self) -> None:
        """注销许可证"""
        reply = QtWidgets.QMessageBox.warning(
            self,
            "确认注销",
            "确定要注销当前许可证吗？注销后软件将自动退出。",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self._license_manager.deactivate()
            QtWidgets.QMessageBox.information(
                self,
                "已注销",
                "许可证已注销，软件即将退出。"
            )
            QtWidgets.QApplication.quit()
