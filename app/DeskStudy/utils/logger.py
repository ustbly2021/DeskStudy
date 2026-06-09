"""
日志配置模块
使用Loguru进行日志管理
"""

import sys
import os
from pathlib import Path
from typing import Optional

from loguru import logger

_logged = False


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days"
) -> None:
    """
    配置Loguru日志

    Args:
        log_level: 日志级别
        log_file: 日志文件路径，如果为None则只输出到控制台
        rotation: 日志轮转大小
        retention: 日志保留天数
    """
    global _logged

    if _logged:
        return

    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 在打包环境中，sys.stderr 可能为 None
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format=log_format,
            level=log_level,
            colorize=True
        )

    # 如果没有指定日志文件，使用默认路径
    if not log_file:
        # 获取日志目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            app_data = os.path.join(os.path.expanduser("~"), ".deskstudy")
        else:
            # 开发环境
            app_data = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")

        os.makedirs(app_data, exist_ok=True)
        log_file = os.path.join(app_data, "deskstudy.log")

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_file),
            format=log_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8"
        )

    _logged = True


def get_logger(name: str = __name__):
    """
    获取日志记录器

    Args:
        name: 模块名称

    Returns:
        logger实例
    """
    return logger.bind(name=name)


def set_log_level(level: str) -> None:
    """动态设置日志级别"""
    logger.configure(handlers=[{"level": level}])
