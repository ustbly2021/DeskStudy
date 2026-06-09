"""
粉笔网题目导入对话框
"""

import os
import sys
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from typing import List, Dict, Any
import threading

from app.DeskStudy.services.fenbi_service import get_fenbi_service
from app.DeskStudy.services.question_service import QuestionService
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)

# 样式定义
INPUT_STYLE = """
    QLineEdit, QTextEdit {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        padding: 8px 12px;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #6366F1;
    }
"""

BUTTON_STYLE = """
    QPushButton {
        background: #6366F1;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: #5558E3;
    }
    QPushButton:disabled {
        background: #4B5563;
    }
"""

SECONDARY_BUTTON_STYLE = """
    QPushButton {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background: rgba(255, 255, 255, 0.15);
    }
"""

LIST_STYLE = """
    QListWidget {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 4px;
    }
    QListWidget::item {
        color: white;
        padding: 8px;
        border-radius: 4px;
    }
    QListWidget::item:selected {
        background: rgba(99, 102, 241, 0.3);
    }
    QListWidget::item:hover {
        background: rgba(255, 255, 255, 0.1);
    }
"""


class FenbiImportDialog(QtWidgets.QDialog):
    """粉笔网题目导入对话框"""

    # 信号定义
    _update_cookie_signal = QtCore.Signal(str, str)  # cookie_str, status_msg
    _update_status_signal = QtCore.Signal(str)  # status_msg
    _enable_button_signal = QtCore.Signal()  # 启用按钮

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fenbi_service = get_fenbi_service()
        self._question_service = QuestionService()
        self._chapters: List[Dict[str, Any]] = []
        self._imported_questions: List[Dict[str, Any]] = []
        self._selenium_driver = None  # 保存 Selenium driver

        self._setup_ui()
        self._auto_load_cookie()

        # 连接信号
        self._update_cookie_signal.connect(self._on_update_cookie)
        self._update_status_signal.connect(self._on_update_status)
        self._enable_button_signal.connect(self._on_enable_button)

        logger.info("粉笔导入对话框初始化完成")

    def _on_update_cookie(self, cookie_str: str, status: str) -> None:
        """更新Cookie和状态"""
        self._cookie_input.setPlainText(cookie_str)
        self._progress_label.setText(status)

    def _on_update_status(self, status: str) -> None:
        """更新状态"""
        self._progress_label.setText(status)

    def _on_enable_button(self) -> None:
        """启用按钮"""
        self._auto_cookie_btn.setEnabled(True)
        self._auto_cookie_btn.setText("自动获取Cookie")

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("从粉笔网导入题目")
        self.setFixedSize(600, 700)
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
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # URL输入
        url_group = QtWidgets.QGroupBox("题目页面地址")
        url_layout = QtWidgets.QVBoxLayout(url_group)

        self._url_input = QtWidgets.QLineEdit()
        self._url_input.setPlaceholderText("请输入粉笔网题目页面URL，如：https://www.fenbi.com/spa/paper/...")
        self._url_input.setStyleSheet(INPUT_STYLE)
        url_layout.addWidget(self._url_input)

        layout.addWidget(url_group)

        # Cookie输入
        cookie_group = QtWidgets.QGroupBox("登录Cookie")
        cookie_layout = QtWidgets.QVBoxLayout(cookie_group)

        cookie_hint = QtWidgets.QLabel(
            "推荐点击\"浏览器登录\"，会打开浏览器让你登录粉笔网，自动获取Cookie\n"
            "\"自动获取Cookie\"需要关闭浏览器，且可能因加密方式不兼容而失败"
        )
        cookie_hint.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        cookie_hint.setWordWrap(True)
        cookie_layout.addWidget(cookie_hint)

        # Cookie按钮行
        cookie_btn_layout = QtWidgets.QHBoxLayout()

        self._auto_cookie_btn = QtWidgets.QPushButton("自动获取Cookie")
        self._auto_cookie_btn.setStyleSheet(BUTTON_STYLE)
        self._auto_cookie_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._auto_cookie_btn.clicked.connect(self._on_auto_cookie)
        cookie_btn_layout.addWidget(self._auto_cookie_btn)

        self._browser_login_btn = QtWidgets.QPushButton("浏览器登录")
        self._browser_login_btn.setStyleSheet("""
            QPushButton {
                background: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:disabled {
                background: #4B5563;
            }
        """)
        self._browser_login_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._browser_login_btn.clicked.connect(self._on_browser_login)
        cookie_btn_layout.addWidget(self._browser_login_btn)

        self._clear_cookie_btn = QtWidgets.QPushButton("清除")
        self._clear_cookie_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self._clear_cookie_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._clear_cookie_btn.clicked.connect(lambda: self._cookie_input.clear())
        cookie_btn_layout.addWidget(self._clear_cookie_btn)

        cookie_btn_layout.addStretch()
        cookie_layout.addLayout(cookie_btn_layout)

        self._cookie_input = QtWidgets.QTextEdit()
        self._cookie_input.setPlaceholderText(
            "或手动粘贴Cookie，支持以下格式：\n"
            "1. 每行一个: name=value\n"
            "2. 浏览器格式: name1=value1; name2=value2"
        )
        self._cookie_input.setMaximumHeight(80)
        self._cookie_input.setStyleSheet(INPUT_STYLE)
        cookie_layout.addWidget(self._cookie_input)

        layout.addWidget(cookie_group)

        # 章节选择
        chapter_group = QtWidgets.QGroupBox("章节选择")
        chapter_layout = QtWidgets.QVBoxLayout(chapter_group)

        chapter_btn_layout = QtWidgets.QHBoxLayout()

        self._fetch_btn = QtWidgets.QPushButton("获取章节列表")
        self._fetch_btn.setStyleSheet(BUTTON_STYLE)
        self._fetch_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._fetch_btn.clicked.connect(self._on_fetch_chapters)
        chapter_btn_layout.addWidget(self._fetch_btn)

        self._select_all_btn = QtWidgets.QPushButton("全选")
        self._select_all_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self._select_all_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._on_select_all)
        self._select_all_btn.setEnabled(False)
        chapter_btn_layout.addWidget(self._select_all_btn)

        chapter_btn_layout.addStretch()

        chapter_layout.addLayout(chapter_btn_layout)

        self._chapter_list = QtWidgets.QListWidget()
        self._chapter_list.setStyleSheet(LIST_STYLE)
        self._chapter_list.setMinimumHeight(150)
        chapter_layout.addWidget(self._chapter_list)

        layout.addWidget(chapter_group)

        # 进度显示
        self._progress_label = QtWidgets.QLabel("")
        self._progress_label.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(self._progress_label)

        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: #6366F1;
                border-radius: 4px;
            }
        """)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # 按钮
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        self._import_btn = QtWidgets.QPushButton("开始导入")
        self._import_btn.setFixedSize(120, 36)
        self._import_btn.setStyleSheet(BUTTON_STYLE)
        self._import_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self._import_btn)

        self._cancel_btn = QtWidgets.QPushButton("取消")
        self._cancel_btn.setFixedSize(100, 36)
        self._cancel_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self._cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

    def _auto_load_cookie(self) -> None:
        """自动加载保存的Cookie"""
        # try:
        #     import os
        #     cookie_dir = os.path.join(os.path.expanduser("~"), ".deskstudy")
        #     cookie_file = os.path.join(cookie_dir, "fenbi_cookie.txt")

        #     if os.path.exists(cookie_file):
        #         with open(cookie_file, 'r', encoding='utf-8') as f:
        #             self._cookie_input.setPlainText(f.read().strip())
        # except Exception:
        #     pass
        pass
    def _save_cookie(self) -> None:
        """保存Cookie"""
        try:
            import os
            cookie_dir = os.path.join(os.path.expanduser("~"), ".deskstudy")
            os.makedirs(cookie_dir, exist_ok=True)
            cookie_file = os.path.join(cookie_dir, "fenbi_cookie.txt")

            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(self._cookie_input.toPlainText().strip())
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")

    def _on_browser_login(self) -> None:
        """浏览器登录获取Cookie"""
        self._browser_login_btn.setEnabled(False)
        self._browser_login_btn.setText("启动中...")
        self._progress_label.setText("正在启动浏览器...")

        threading.Thread(target=self._browser_login_thread, daemon=True).start()

    def _browser_login_thread(self) -> None:
        """线程：打开浏览器让用户登录"""
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            import time
            import os

            # 尝试使用 webdriver_manager
            options = Options()
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=1280,800')

            # 使用用户现有的 Edge 配置文件（这样就有登录状态）
            edge_user_data = os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data")
            if os.path.exists(edge_user_data):
                options.add_argument(f'--user-data-dir={edge_user_data}')
                options.add_argument('--profile-directory=Default')
                logger.info("使用Edge默认配置文件")

            # 尝试多种方式启动浏览器
            driver_started = False
            errors = []

            # 方式1: 使用打包的或本地的 msedgedriver.exe
            driver_paths = []

            # PyInstaller 打包后的路径
            if getattr(sys, 'frozen', False):
                # 单文件模式：解压到 sys._MEIPASS
                driver_paths.append(os.path.join(sys._MEIPASS, "msedgedriver.exe"))
                # 目录模式：在 exe 同级目录
                driver_paths.append(os.path.join(os.path.dirname(sys.executable), "msedgedriver.exe"))

            # 开发环境：从 fenbi_import_dialog.py 往上走4层到项目根目录
            driver_paths.append(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "msedgedriver.exe"
            ))

            for local_driver_path in driver_paths:
                logger.debug(f"检查 EdgeDriver 路径: {local_driver_path}")
                if os.path.exists(local_driver_path):
                    try:
                        from selenium.webdriver.edge.service import Service as EdgeService
                        logger.info(f"使用 EdgeDriver: {local_driver_path}")
                        service = EdgeService(executable_path=local_driver_path)
                        self._selenium_driver = webdriver.Edge(service=service, options=options)
                        driver_started = True
                        logger.info("EdgeDriver 启动成功")
                        break
                    except Exception as e:
                        errors.append(f"EdgeDriver ({local_driver_path}): {e}")
                        logger.warning(f"EdgeDriver 失败: {e}")

            # 方式2: 使用 webdriver_manager 自动下载驱动（需要联网）
            if not driver_started:
                try:
                    from webdriver_manager.microsoft import EdgeChromiumDriverManager
                    from selenium.webdriver.edge.service import Service as EdgeService
                    logger.info("尝试使用 webdriver_manager 启动 Edge...")
                    service = EdgeService(EdgeChromiumDriverManager().install())
                    self._selenium_driver = webdriver.Edge(service=service, options=options)
                    driver_started = True
                    logger.info("webdriver_manager 启动成功")
                except Exception as e:
                    errors.append(f"webdriver_manager: {e}")
                    logger.warning(f"webdriver_manager 失败: {e}")

            # 方式3: 使用系统 PATH 中的 EdgeDriver
            if not driver_started:
                try:
                    logger.info("尝试使用系统 PATH 中的 EdgeDriver...")
                    self._selenium_driver = webdriver.Edge(options=options)
                    driver_started = True
                    logger.info("系统 PATH EdgeDriver 启动成功")
                except Exception as e:
                    errors.append(f"系统 PATH: {e}")
                    logger.warning(f"系统 PATH EdgeDriver 失败: {e}")

            # 方式4: 尝试使用 Chrome
            if not driver_started:
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service as ChromeService
                    logger.info("尝试使用 Chrome 浏览器...")
                    chrome_options = webdriver.ChromeOptions()
                    chrome_options.add_argument('--headless=new')
                    chrome_options.add_argument('--disable-gpu')
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--window-size=1280,800')

                    chrome_user_data = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
                    if os.path.exists(chrome_user_data):
                        chrome_options.add_argument(f'--user-data-dir={chrome_user_data}')
                        chrome_options.add_argument('--profile-directory=Default')

                    service = ChromeService(ChromeDriverManager().install())
                    self._selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver_started = True
                    logger.info("Chrome 启动成功")
                except Exception as e:
                    errors.append(f"Chrome: {e}")
                    logger.warning(f"Chrome 失败: {e}")

            if not driver_started:
                error_msg = "无法启动浏览器，请检查：\n"
                error_msg += "1. 确保已安装 Edge 或 Chrome 浏览器\n"
                error_msg += "2. 或手动粘贴 Cookie\n"
                error_msg += f"\n详细错误: {'; '.join(errors)}"
                raise Exception(error_msg)

            self._update_status_signal.emit("浏览器已打开，正在访问粉笔网...")

            # 访问粉笔网
            self._selenium_driver.get('https://www.fenbi.com')
            time.sleep(3)

            # 检查是否已登录
            current_url = self._selenium_driver.current_url
            if 'login' in current_url.lower():
                self._update_status_signal.emit("请在浏览器中登录粉笔网，登录后点击下方按钮获取Cookie")
            else:
                self._update_status_signal.emit("检测到已登录，点击下方按钮获取Cookie")

            # 使用 invokeMethod 在主线程中更新按钮
            QtCore.QMetaObject.invokeMethod(
                self,
                "_setup_extract_cookie_button",
                QtCore.Qt.QueuedConnection
            )

        except Exception as e:
            if self._selenium_driver:
                try:
                    self._selenium_driver.quit()
                except:
                    pass
                self._selenium_driver = None
            logger.error(f"启动浏览器失败: {e}")
            self._update_status_signal.emit(f"启动浏览器失败: {str(e)}")
            self._enable_button_signal.emit()
            self._browser_login_btn.setText("浏览器登录")

    @QtCore.Slot()
    def _setup_extract_cookie_button(self) -> None:
        """在主线程中设置提取Cookie按钮"""
        self._browser_login_btn.setText("获取Cookie")
        self._browser_login_btn.setEnabled(True)
        try:
            self._browser_login_btn.clicked.disconnect()
        except:
            pass
        self._browser_login_btn.clicked.connect(self._extract_cookies_from_driver)

    @QtCore.Slot()
    def _extract_cookies_from_driver(self) -> None:
        """从Selenium driver中提取Cookie"""
        logger.info("开始提取Cookie...")
        try:
            self._browser_login_btn.setEnabled(False)
            self._browser_login_btn.setText("获取中...")
            self._progress_label.setText("正在提取Cookie...")

            if not self._selenium_driver:
                self._update_status_signal.emit("浏览器已关闭，请重新点击浏览器登录")
                self._browser_login_btn.setText("浏览器登录")
                self._browser_login_btn.setEnabled(True)
                return

            # 获取所有Cookie
            selenium_cookies = self._selenium_driver.get_cookies()
            logger.info(f"获取到 {len(selenium_cookies)} 个Cookie")

            # 关闭浏览器
            try:
                self._selenium_driver.quit()
            except:
                pass
            self._selenium_driver = None

            if not selenium_cookies:
                self._update_status_signal.emit("未获取到Cookie，请确保已登录粉笔网")
                self._browser_login_btn.setText("浏览器登录")
                self._browser_login_btn.setEnabled(True)
                return

            # 转换为字符串格式
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in selenium_cookies])
            self._cookie_input.setPlainText(cookie_str)
            self._progress_label.setText(f"成功获取 {len(selenium_cookies)} 个Cookie")

            # 重置按钮
            self._browser_login_btn.setText("浏览器登录")
            self._browser_login_btn.setEnabled(True)
            try:
                self._browser_login_btn.clicked.disconnect()
            except:
                pass
            self._browser_login_btn.clicked.connect(self._on_browser_login)

        except Exception as e:
            logger.error(f"提取Cookie失败: {e}")
            if self._selenium_driver:
                try:
                    self._selenium_driver.quit()
                except:
                    pass
                self._selenium_driver = None
            self._progress_label.setText(f"获取Cookie失败: {str(e)}")
            self._browser_login_btn.setText("浏览器登录")
            self._browser_login_btn.setEnabled(True)
            try:
                self._browser_login_btn.clicked.disconnect()
            except:
                pass
            self._browser_login_btn.clicked.connect(self._on_browser_login)

    def _on_auto_cookie(self) -> None:
        """自动获取Cookie"""
        self._auto_cookie_btn.setEnabled(False)
        self._auto_cookie_btn.setText("正在获取...")
        self._progress_label.setText("正在从浏览器读取Cookie...")

        # 使用线程获取
        threading.Thread(target=self._fetch_cookie_thread, daemon=True).start()

    def _fetch_cookie_thread(self) -> None:
        """线程：获取Cookie"""
        try:
            cookies = self._read_browser_cookies("fenbi.com")
            if cookies:
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                # 更新UI - 使用信号
                self._update_cookie_signal.emit(cookie_str, f"成功获取 {len(cookies)} 个Cookie")
            else:
                self._update_status_signal.emit("未找到Cookie，请确保已在浏览器中登录粉笔网")
        except Exception as e:
            self._update_status_signal.emit(f"获取失败: {str(e)}")
        finally:
            self._enable_button_signal.emit()

    def _read_browser_cookies(self, domain: str) -> List[Dict[str, str]]:
        """从浏览器读取Cookie"""
        import os

        cookies = []

        # 方式1: 使用 rookiepy 库（最可靠）
        try:
            import rookiepy
            for browser_fn, browser_name in [
                (rookiepy.edge, 'edge'),
                (rookiepy.chrome, 'chrome'),
            ]:
                try:
                    browser_cookies = browser_fn(domains=[domain])
                    for c in browser_cookies:
                        name = c.get('name', '')
                        value = c.get('value', '')
                        if name and value and len(value) > 5:
                            cookies.append({'name': name, 'value': value})
                    if cookies:
                        logger.info(f"通过rookiepy从{browser_name}获取 {len(cookies)} 个Cookie")
                        return cookies
                except Exception as e:
                    logger.debug(f"rookiepy {browser_name} 失败: {e}")
        except ImportError:
            logger.info("rookiepy未安装，使用手动解密方式")

        # 方式2: 手动解密
        return self._read_browser_cookies_manual(domain)

    def _read_browser_cookies_manual(self, domain: str) -> List[Dict[str, str]]:
        """手动从浏览器读取Cookie（备用方案）"""
        import os
        import sqlite3
        import shutil
        import tempfile
        import base64
        import json
        import subprocess

        cookies = []

        # 检查浏览器进程
        def check_browser_process():
            running_browsers = []
            try:
                result = subprocess.run(['tasklist'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout.lower()
                if 'chrome.exe' in output:
                    running_browsers.append('Chrome')
                if 'msedge.exe' in output:
                    running_browsers.append('Edge')
            except:
                pass
            return running_browsers

        # 查找所有浏览器Cookie文件
        all_paths = []
        for browser_base, browser_label in [
            (os.path.expanduser("~/AppData/Local/Google/Chrome/User Data"), "Chrome"),
            (os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data"), "Edge"),
        ]:
            if not os.path.exists(browser_base):
                continue
            local_state = os.path.join(browser_base, 'Local State')
            for profile in ['Default', 'Profile 1', 'Profile 2', 'Profile 3']:
                profile_path = os.path.join(browser_base, profile)
                if not os.path.exists(profile_path):
                    continue
                for cookie_file in ['Network/Cookies', 'Cookies']:
                    cookie_path = os.path.join(profile_path, cookie_file)
                    if os.path.exists(cookie_path):
                        all_paths.append((cookie_path, local_state, f"{browser_label}-{profile}"))

        if not all_paths:
            raise Exception("未找到浏览器Cookie文件\n\n请确保：\n1. 已安装 Chrome 或 Edge 浏览器\n2. 已在浏览器中登录粉笔网\n\n或手动粘贴Cookie")

        logger.info(f"找到 {len(all_paths)} 个可能的Cookie文件路径")

        permission_errors = []
        found_files = []

        for cookie_path, local_state_path, browser_name in all_paths:
            found_files.append(browser_name)

            try:
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, 'fenbi_cookies_temp.db')
                try:
                    shutil.copy2(cookie_path, temp_path)
                except PermissionError:
                    permission_errors.append(browser_name)
                    continue

                # 获取加密密钥
                encryption_key = None
                if os.path.exists(local_state_path):
                    try:
                        encryption_key = self._get_chrome_encryption_key(local_state_path)
                        logger.info(f"成功获取加密密钥: {browser_name}, 密钥长度: {len(encryption_key) if encryption_key else 0}")
                    except Exception as e:
                        logger.warning(f"获取加密密钥失败: {browser_name} - {e}")

                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name, encrypted_value, host_key FROM cookies")
                all_cookies = cursor.fetchall()
                logger.info(f"{browser_name} 共有 {len(all_cookies)} 个Cookie")

                fenbi_cookies = [c for c in all_cookies if any(d in (c[2] or '').lower() for d in ['fenbi', 'fbcontent'])]
                logger.info(f"{browser_name} 粉笔网相关Cookie: {len(fenbi_cookies)} 个")

                for row in fenbi_cookies:
                    name = row[0]
                    encrypted_value = row[1]
                    host = row[2]
                    value = None

                    prefix = encrypted_value[:3] if len(encrypted_value) >= 3 else b''

                    # v10/v11: AES-GCM
                    if prefix in [b'v10', b'v11'] and encryption_key:
                        try:
                            value = self._decrypt_chrome_cookie(encrypted_value, encryption_key)
                        except Exception as e:
                            logger.warning(f"AES解密失败 {name}: {e}")

                    # 非v10/v11: DPAPI
                    if not value and prefix not in [b'v10', b'v11']:
                        try:
                            import win32crypt
                            decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)
                            value = decrypted[1].decode('utf-8', errors='ignore')
                        except:
                            try:
                                value = self._decrypt_with_dpapi(encrypted_value)
                            except:
                                pass

                    # 明文
                    if not value and not prefix.startswith(b'v'):
                        try:
                            value = encrypted_value.decode('utf-8')
                        except:
                            pass

                    if value and len(value) > 5:
                        printable_count = sum(1 for c in value if c.isprintable() or c in '\n\r\t')
                        if printable_count > len(value) * 0.8:
                            cookies.append({'name': name, 'value': value})
                            logger.info(f"添加Cookie: {name}")
                        else:
                            logger.warning(f"Cookie包含乱码，跳过: {name}")
                    else:
                        logger.warning(f"Cookie解密失败: {name} (host: {host}, 前缀: {prefix})")

                conn.close()
                try:
                    os.remove(temp_path)
                except:
                    pass

                if cookies:
                    return cookies

            except Exception as e:
                logger.error(f"读取 {browser_name} 失败: {e}")
                continue

        if permission_errors:
            running = check_browser_process()
            if running:
                raise Exception(f"检测到 {', '.join(running)} 浏览器正在运行\n请完全关闭浏览器后重试")
            else:
                raise Exception(f"无法读取Cookie文件，请检查任务管理器中是否有浏览器后台进程")
        
        raise Exception(f"已找到 {len(found_files)} 个浏览器配置，但未找到粉笔网Cookie\n\n请确保已在浏览器中登录粉笔网")

    def _get_chrome_encryption_key(self, local_state_path: str):
        """获取Chrome/Edge的加密密钥"""
        import json
        import base64
        import ctypes
        from ctypes import wintypes

        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)

        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        # 去掉DPAPI前缀 "DPAPI"
        encrypted_key = encrypted_key[5:]
        
        logger.debug(f"加密密钥长度: {len(encrypted_key)}")
        
        # 方式1: 使用 ctypes 调用 Windows DPAPI（优先，更可靠）
        try:
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [
                    ('cbData', wintypes.DWORD),
                    ('pbData', ctypes.POINTER(ctypes.c_byte))
                ]
            
            blob_in = DATA_BLOB()
            blob_in.cbData = len(encrypted_key)
            blob_in.pbData = (ctypes.c_byte * len(encrypted_key))(*encrypted_key)
            
            blob_out = DATA_BLOB()
            
            # 调用 CryptUnprotectData
            result = ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(blob_in),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(blob_out)
            )
            
            if result:
                buffer = ctypes.create_string_buffer(blob_out.cbData)
                ctypes.memmove(buffer, blob_out.pbData, blob_out.cbData)
                decrypted_key = buffer.raw
                # 释放内存
                ctypes.windll.kernel32.LocalFree(blob_out.pbData)
                logger.info("成功通过ctypes解密浏览器密钥")
                return decrypted_key
            else:
                error = ctypes.get_last_error()
                logger.warning(f"ctypes CryptUnprotectData 失败，错误码: {error}")
        except Exception as e:
            logger.warning(f"ctypes解密密钥失败: {e}")
        
        # 方式2: 使用 win32crypt（备选）
        try:
            import win32crypt
            decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            logger.info("成功通过win32crypt解密浏览器密钥")
            return decrypted_key
        except Exception as e:
            logger.warning(f"win32crypt解密密钥失败: {e}")
        
        raise Exception("无法解密浏览器密钥")

    def _decrypt_with_dpapi(self, encrypted_data: bytes) -> str:
        """使用ctypes调用Windows DPAPI解密数据"""
        import ctypes
        from ctypes import wintypes
        
        crypt32 = ctypes.windll.crypt32
        
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_byte))
            ]
        
        blob_in = DATA_BLOB()
        blob_in.cbData = len(encrypted_data)
        blob_in.pbData = (ctypes.c_byte * len(encrypted_data))(*encrypted_data)
        
        blob_out = DATA_BLOB()
        
        if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            buffer = ctypes.create_string_buffer(blob_out.cbData)
            ctypes.memmove(buffer, blob_out.pbData, blob_out.cbData)
            result = buffer.raw.decode('utf-8', errors='ignore')
            # 释放内存
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return result
        
        raise Exception("DPAPI解密失败")

    def _decrypt_chrome_cookie(self, encrypted_value: bytes, key: bytes) -> str:
        """解密新版Chrome/Edge的Cookie"""
        try:
            from Crypto.Cipher import AES
        except ImportError:
            try:
                from Cryptodome.Cipher import AES
            except ImportError:
                raise ImportError("请安装 pycryptodome: pip install pycryptodome")

        # v10格式: version(3) + nonce(12) + ciphertext + tag(16)
        nonce = encrypted_value[3:15]
        ciphertext_tag = encrypted_value[15:]
        
        # AES-GCM: ciphertext和tag在一起，需要分开
        # tag是最后16字节
        if len(ciphertext_tag) < 16:
            raise Exception(f"加密数据太短: {len(ciphertext_tag)}")
        
        ciphertext = ciphertext_tag[:-16]
        tag = ciphertext_tag[-16:]

        logger.debug(f"AES解密: nonce长度={len(nonce)}, ciphertext长度={len(ciphertext)}, tag长度={len(tag)}, key长度={len(key)}")

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode('utf-8')

    def _on_fetch_chapters(self) -> None:
        """获取章节列表"""
        url = self._url_input.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "提示", "请输入题目页面URL")
            return

        if 'fenbi.com' not in url:
            QtWidgets.QMessageBox.warning(self, "提示", "请输入有效的粉笔网URL")
            return

        cookie_text = self._cookie_input.toPlainText().strip()
        if not cookie_text:
            QtWidgets.QMessageBox.warning(self, "提示", "请输入登录Cookie")
            return

        # 保存Cookie
        self._save_cookie()

        # 解析Cookie
        cookies = self._fenbi_service.parse_cookies(cookie_text)
        if not cookies:
            QtWidgets.QMessageBox.warning(self, "提示", "Cookie格式无效")
            return

        # 禁用按钮，显示进度
        self._fetch_btn.setEnabled(False)
        self._fetch_btn.setText("正在获取...")
        self._progress_label.setText("正在获取章节列表，请稍候...")
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)  # 不确定进度

        # 使用线程获取
        self._fetch_thread = FetchChapterThread(url, cookies)
        self._fetch_thread.signals.finished.connect(self._on_fetch_finished)
        self._fetch_thread.signals.error.connect(self._on_fetch_error)
        self._fetch_thread.start()

    def _on_fetch_finished(self, chapters: List[Dict[str, Any]]) -> None:
        """获取章节完成"""
        self._chapters = chapters
        self._fetch_btn.setEnabled(True)
        self._fetch_btn.setText("获取章节列表")
        self._progress_bar.setVisible(False)
        self._progress_label.setText(f"找到 {len(chapters)} 个章节，请选择要导入的章节")

        # 更新列表
        self._chapter_list.clear()
        for ch in chapters:
            item = QtWidgets.QListWidgetItem(f"{ch['name']} ({ch['count']}题)")
            item.setData(QtCore.Qt.UserRole, ch['name'])
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            self._chapter_list.addItem(item)

        self._select_all_btn.setEnabled(True)

    def _on_fetch_error(self, error: str) -> None:
        """获取章节失败"""
        self._fetch_btn.setEnabled(True)
        self._fetch_btn.setText("获取章节列表")
        self._progress_bar.setVisible(False)
        self._progress_label.setText("")
        QtWidgets.QMessageBox.critical(self, "错误", error)

    def _on_select_all(self) -> None:
        """全选/取消全选"""
        all_checked = all(
            self._chapter_list.item(i).checkState() == QtCore.Qt.Checked
            for i in range(self._chapter_list.count())
        )

        state = QtCore.Qt.Unchecked if all_checked else QtCore.Qt.Checked
        for i in range(self._chapter_list.count()):
            self._chapter_list.item(i).setCheckState(state)

    def _on_import(self) -> None:
        """开始导入"""
        if not self._chapters:
            QtWidgets.QMessageBox.warning(self, "提示", "请先获取章节列表")
            return

        # 获取选中的章节
        selected = []
        for i in range(self._chapter_list.count()):
            item = self._chapter_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected.append(item.data(QtCore.Qt.UserRole))

        if not selected:
            QtWidgets.QMessageBox.warning(self, "提示", "请至少选择一个章节")
            return

        # 获取Cookie
        cookie_text = self._cookie_input.toPlainText().strip()
        cookies = self._fenbi_service.parse_cookies(cookie_text)

        # 禁用按钮
        self._import_btn.setEnabled(False)
        self._import_btn.setText("正在导入...")
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._progress_bar.setRange(0, 100)

        # 使用线程导入
        self._import_thread = ImportThread(
            self._url_input.text().strip(),
            cookies,
            selected
        )
        self._import_thread.signals.progress.connect(self._on_import_progress)
        self._import_thread.signals.finished.connect(self._on_import_finished)
        self._import_thread.signals.error.connect(self._on_import_error)
        self._import_thread.start()

    def _on_import_progress(self, message: str, current: int, total: int) -> None:
        """导入进度更新"""
        self._progress_label.setText(message)
        if total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)

    def _on_import_finished(self, questions: List[Dict[str, Any]]) -> None:
        """导入完成"""
        self._imported_questions = questions
        self._import_btn.setEnabled(True)
        self._import_btn.setText("开始导入")
        self._progress_bar.setVisible(False)

        # 保存到数据库
        try:
            count = self._question_service.import_questions(questions)
            QtWidgets.QMessageBox.information(
                self,
                "导入成功",
                f"成功导入 {count} 道题目"
            )
            logger.info(f"粉笔导入成功: {count} 题")
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "保存失败",
                f"保存题目失败: {str(e)}"
            )
            logger.error(f"保存题目失败: {e}")

    def _on_import_error(self, error: str) -> None:
        """导入失败"""
        self._import_btn.setEnabled(True)
        self._import_btn.setText("开始导入")
        self._progress_bar.setVisible(False)
        self._progress_label.setText("")
        QtWidgets.QMessageBox.critical(self, "错误", error)

    def closeEvent(self, event) -> None:
        """关闭事件"""
        self._fenbi_service.stop()
        super().closeEvent(event)


class WorkerSignals(QtCore.QObject):
    """工作线程信号"""
    finished = QtCore.Signal(object)
    error = QtCore.Signal(str)
    progress = QtCore.Signal(str, int, int)


class FetchChapterThread(QtCore.QThread):
    """获取章节线程"""

    def __init__(self, url: str, cookies: List[Dict[str, str]]):
        super().__init__()
        self._url = url
        self._cookies = cookies
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            service = get_fenbi_service()
            chapters = service.fetch_chapters(self._url, self._cookies)
            self.signals.finished.emit(chapters)
        except Exception as e:
            self.signals.error.emit(str(e))


class ImportThread(QtCore.QThread):
    """导入题目线程"""

    def __init__(self, url: str, cookies: List[Dict[str, str]], chapters: List[str]):
        super().__init__()
        self._url = url
        self._cookies = cookies
        self._chapters = chapters
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            service = get_fenbi_service()

            def progress(msg, cur, total):
                self.signals.progress.emit(msg, cur, total)

            questions = service.import_questions(
                self._url,
                self._cookies,
                self._chapters,
                progress
            )

            self.signals.finished.emit(questions)
        except Exception as e:
            self.signals.error.emit(str(e))
