"""
DeskStudy 配置管理
使用Pydantic进行配置验证和管理
"""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class FloatingBallConfig(BaseModel):
    """悬浮球配置"""
    size: int = Field(default=40, ge=24, le=64)
    opacity: float = Field(default=0.9, ge=0.1, le=1.0)
    expand_distance: int = Field(default=10, ge=0, le=50)
    auto_hide_delay: int = Field(default=3000, ge=1000, le=10000)
    edge_snap_enabled: bool = True
    mouse_penetrate: bool = False


class HotkeyConfig(BaseModel):
    """热键配置"""
    boss_key: str = "Ctrl+Shift+B"
    pause_key: str = "Ctrl+Shift+P"


class StudyConfig(BaseModel):
    """学习配置"""
    question_interval: int = Field(default=30, ge=10, le=300)
    show_explanation: bool = True
    auto_next_delay: int = Field(default=2000, ge=1000, le=5000)


class Settings(BaseModel):
    """应用全局配置"""
    floating_ball: FloatingBallConfig = Field(default_factory=FloatingBallConfig)
    hotkey: HotkeyConfig = Field(default_factory=HotkeyConfig)
    study: StudyConfig = Field(default_factory=StudyConfig)

    auto_start: bool = False
    question_bank_path: str = ""
    mute_mode: bool = False
    fullscreen_pause: bool = True

    class Config:
        env_prefix = "DESKSTUDY_"


_settings: Optional[Settings] = None
_config_path = Path.home() / ".deskstudy" / "config.json"


def get_settings() -> Settings:
    """获取全局配置单例"""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def load_settings() -> Settings:
    """从文件加载配置"""
    global _config_path

    if _config_path.exists():
        try:
            with open(_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Settings(**data)
        except Exception:
            pass

    return Settings()


def save_settings(settings: Settings) -> None:
    """保存配置到文件"""
    global _config_path

    _config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(_config_path, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=4, ensure_ascii=False)


def reset_settings() -> Settings:
    """重置配置为默认值"""
    global _settings
    _settings = Settings()
    save_settings(_settings)
    return _settings
