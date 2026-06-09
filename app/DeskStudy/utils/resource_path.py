"""
资源文件路径工具
用于获取打包后的资源文件路径
"""

import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径
    兼容开发环境和打包后的环境

    Args:
        relative_path: 相对路径，如 "sample_questions.json"

    Returns:
        资源文件的绝对路径
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境，使用项目根目录
        base_path = Path(__file__).parent.parent.parent.parent

    return base_path / relative_path


def get_data_dir() -> Path:
    """
    获取用户数据目录（用于存储数据库、配置等）
    打包后数据存储在用户目录下

    Returns:
        用户数据目录路径
    """
    data_dir = Path.home() / ".deskstudy"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
