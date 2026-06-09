"""
配置服务
"""

from typing import Any, Optional, Dict

from sqlalchemy.orm import Session

from app.DeskStudy.database.connection import get_database
from app.DeskStudy.models.user_config import UserConfig
from app.DeskStudy.config.settings import Settings, save_settings, get_settings
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigService:
    """配置服务"""

    def __init__(self):
        self.db = get_database()

    def get_session(self) -> Session:
        return self.db.get_session()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        session = self.get_session()
        try:
            config = session.query(UserConfig).filter(
                UserConfig.key == key
            ).first()

            if config:
                return config.getTypedValue()
            return default
        finally:
            session.close()

    def set(self, key: str, value: Any, description: str = None) -> None:
        """设置配置值"""
        session = self.get_session()
        try:
            config = session.query(UserConfig).filter(
                UserConfig.key == key
            ).first()

            if config:
                config.setTypedValue(value)
                config.description = description or config.description
            else:
                config = UserConfig(key=key, description=description)
                config.setTypedValue(value)
                session.add(config)

            session.commit()
            logger.info(f"设置配置: {key}={value}")
        except Exception as e:
            session.rollback()
            logger.error(f"设置配置失败: {e}")
            raise
        finally:
            session.close()

    def delete(self, key: str) -> bool:
        """删除配置"""
        session = self.get_session()
        try:
            config = session.query(UserConfig).filter(
                UserConfig.key == key
            ).first()

            if config:
                session.delete(config)
                session.commit()
                logger.info(f"删除配置: {key}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除配置失败: {e}")
            raise
        finally:
            session.close()

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        session = self.get_session()
        try:
            configs = session.query(UserConfig).all()
            return {c.key: c.getTypedValue() for c in configs}
        finally:
            session.close()

    def get_app_settings(self) -> Settings:
        """获取应用设置"""
        return get_settings()

    def save_app_settings(self, settings: Settings) -> None:
        """保存应用设置"""
        save_settings(settings)
        logger.info("应用设置已保存")

    def reset_to_default(self) -> Settings:
        """重置为默认设置"""
        from app.DeskStudy.config.settings import reset_settings
        settings = reset_settings()
        logger.info("应用设置已重置")
        return settings
