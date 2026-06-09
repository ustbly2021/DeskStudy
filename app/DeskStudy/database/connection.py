"""
数据库连接管理
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.DeskStudy.config.settings import get_settings
from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()

_engine = None
_session_factory = None
_local = threading.local()


class Database:
    """数据库管理类"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._get_default_db_path()
        self.engine = None
        self.session_factory = None
        self._initialize()

    def _get_default_db_path(self) -> Path:
        """获取默认数据库路径"""
        app_dir = Path.home() / ".deskstudy"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir / "deskstudy.db"

    def _initialize(self) -> None:
        """初始化数据库引擎"""
        db_url = f"sqlite:///{self.db_path}"

        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )

    def create_tables(self) -> None:
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    def migrate_database(self) -> None:
        """数据库迁移 - 添加新字段"""
        try:
            # 检查并添加 correct_rate 字段
            self._add_column_if_not_exists('questions', 'correct_rate', 'REAL DEFAULT 0.0')
            # 检查并添加 source 字段
            self._add_column_if_not_exists('questions', 'source', 'VARCHAR(200)')
            logger.info("数据库迁移完成")
        except Exception as e:
            logger.warning(f"数据库迁移失败: {e}")

    def _add_column_if_not_exists(self, table: str, column: str, column_type: str) -> None:
        """如果列不存在则添加"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 检查列是否存在
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        if column not in columns:
            logger.info(f"添加新字段: {table}.{column}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            conn.commit()

        conn.close()

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        return self.session_factory()

    def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()


_database: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库单例"""
    global _database
    if _database is None:
        settings = get_settings()
        db_path = settings.question_bank_path if settings.question_bank_path else None
        _database = Database(db_path)
        _database.create_tables()
        _database.migrate_database()  # 执行数据库迁移
    return _database


def init_database() -> Database:
    """初始化数据库"""
    db = get_database()
    return db
