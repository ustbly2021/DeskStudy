"""
用户配置模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float

from app.DeskStudy.database.connection import Base


class UserConfig(Base):
    """用户配置表"""
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值")
    value_type = Column(String(20), default="string", comment="值类型: string/int/float/bool/json")
    description = Column(String(500), nullable=True, comment="描述")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"<UserConfig(key={self.key}, value={self.value})>"

    def getTypedValue(self):
        """获取类型化值"""
        if self.value_type == "int":
            return int(self.value) if self.value else 0
        elif self.value_type == "float":
            return float(self.value) if self.value else 0.0
        elif self.value_type == "bool":
            return self.value == "true" if self.value else False
        elif self.value_type == "json":
            import json
            return json.loads(self.value) if self.value else None
        return self.value

    def setTypedValue(self, value) -> None:
        """设置类型化值"""
        if isinstance(value, bool):
            self.value = "true" if value else "false"
            self.value_type = "bool"
        elif isinstance(value, int):
            self.value = str(value)
            self.value_type = "int"
        elif isinstance(value, float):
            self.value = str(value)
            self.value_type = "float"
        elif isinstance(value, dict) or isinstance(value, list):
            import json
            self.value = json.dumps(value)
            self.value_type = "json"
        else:
            self.value = str(value)
            self.value_type = "string"
