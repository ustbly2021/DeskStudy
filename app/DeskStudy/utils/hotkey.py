"""
热键管理模块
"""

import time
from typing import Callable, Dict, Optional, Tuple
from threading import Thread

from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class HotkeyManager:
    """热键管理器"""

    def __init__(self):
        self._hotkeys: Dict[Tuple, Callable] = {}
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._pressed_keys: set = set()
        self._suppress = False

    def register(self, hotkey_str: str, callback: Callable) -> bool:
        try:
            keys = self._parse_hotkey(hotkey_str)
            if keys:
                self._hotkeys[tuple(keys)] = callback
                logger.info(f"注册热键: {hotkey_str} -> 解析结果: {tuple(keys)}")
                return True
            else:
                logger.error(f"注册热键失败，解析结果为空: {hotkey_str}")
        except Exception as e:
            logger.error(f"注册热键失败: {e}")
        return False

    def unregister(self, hotkey_str: str) -> bool:
        """注销热键"""
        try:
            keys = self._parse_hotkey(hotkey_str)
            if keys and tuple(keys) in self._hotkeys:
                del self._hotkeys[tuple(keys)]
                logger.info(f"注销热键: {hotkey_str}")
                return True
        except Exception as e:
            logger.error(f"注销热键失败: {e}")
        return False

    def _parse_hotkey(self, hotkey_str: str) -> Optional[Tuple]:
        """解析热键字符串"""
        keys = []
        parts = [p.strip() for p in hotkey_str.split("+")]

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part.lower() == "ctrl":
                keys.append("ctrl")
            elif part.lower() == "shift":
                keys.append("shift")
            elif part.lower() == "alt":
                keys.append("alt")
            elif part.lower() == "cmd" or part.lower() == "win":
                keys.append("cmd")
            elif len(part) == 1:
                keys.append(part.lower())
            else:
                try:
                    key = getattr(Key, part.lower())
                    keys.append(key)
                except AttributeError:
                    logger.warning(f"未知热键: {part}")
                    return None

        return tuple(keys) if keys else None

    def start(self) -> None:
        """启动热键监听"""
        if self._running:
            return

        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=self._suppress
        )
        self._listener.start()
        logger.info("热键监听已启动")

    def stop(self) -> None:
        """停止热键监听"""
        if not self._running:
            return

        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("热键监听已停止")

    def _normalize_key(self, key) -> str:
        """将按键标准化为通用名称"""
        if key in (Key.ctrl_l, Key.ctrl_r):
            return "ctrl"
        elif key in (Key.shift_l, Key.shift_r):
            return "shift"
        elif key in (Key.alt_l, Key.alt_r, Key.alt_gr):
            return "alt"
        elif key in (Key.cmd_l, Key.cmd_r):
            return "cmd"
        elif isinstance(key, KeyCode):
            if key.char and len(key.char) == 1 and key.char.isalpha():
                return key.char.lower()
            if key.vk:
                if 65 <= key.vk <= 90:
                    return chr(key.vk).lower()
                elif 48 <= key.vk <= 57:
                    return chr(key.vk)
            if key.char:
                return key.char.lower()
        return str(key)

    def _on_press(self, key) -> None:
        """按键按下处理"""
        try:
            normalized = self._normalize_key(key)
            self._pressed_keys.add(normalized)
            # logger.info(f"按键按下: {normalized}, 当前按键集: {self._pressed_keys}")

            for hotkey_keys, callback in self._hotkeys.items():
                match = all(k in self._pressed_keys for k in hotkey_keys)
                # logger.info(f"匹配检查: 注册={hotkey_keys}, 匹配={match}")
                if match:
                    logger.info(f"热键匹配成功: {hotkey_keys}, 触发回调")
                    try:
                        callback()
                        logger.info("回调执行完毕")
                    except Exception as cb_err:
                        logger.error(f"回调执行异常: {cb_err}")
                    break
        except Exception as e:
            logger.error(f"热键处理错误: {e}")

    def _on_release(self, key) -> None:
        """按键释放处理"""
        try:
            normalized = self._normalize_key(key)
            self._pressed_keys.discard(normalized)
        except Exception as e:
            logger.error(f"热键释放错误: {e}")

    def set_suppress(self, suppress: bool) -> None:
        """设置是否阻止按键传递"""
        self._suppress = suppress


_hotkey_manager: Optional[HotkeyManager] = None


def get_hotkey_manager() -> HotkeyManager:
    """获取热键管理器单例"""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = HotkeyManager()
    return _hotkey_manager
