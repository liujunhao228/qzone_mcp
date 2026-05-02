from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config import config
from ..logging import get_logger
from .models import Base

logger = get_logger(__name__)


class DatabaseManager:
    """数据库管理器 - 负责数据库连接、初始化和会话管理"""
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._initialized = False
    
    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        if not self._engine:
            raise RuntimeError("数据库引擎未初始化，请先调用 initialize()")
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """获取会话工厂"""
        if not self._session_factory:
            raise RuntimeError("会话工厂未初始化，请先调用 initialize()")
        return self._session_factory
    
    async def initialize(self, db_path: Optional[Path] = None) -> None:
        """初始化数据库连接和表结构"""
        if self._initialized:
            return
        
        # 设置数据库路径
        if db_path is None:
            # 确保数据目录存在
            config.ensure_data_dir()
            db_path = config.data_dir / "qzone.db"
            database_url = f"sqlite+aiosqlite:///{db_path}"
        elif str(db_path) == ":memory:":
            # 内存数据库
            database_url = "sqlite+aiosqlite:///:memory:"
        else:
            # 如果提供了数据库路径，确保其父目录存在
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite+aiosqlite:///{db_path}"
        self._engine = create_async_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False}
        )
        
        # 创建会话工厂
        self._session_factory = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # 创建表结构
        async with self._engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys = ON"))
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"数据库初始化完成，路径: {db_path}")
        self._initialized = True
    
    async def get_session(self) -> AsyncSession:
        """获取新的数据库会话"""
        if not self._session_factory:
            await self.initialize()
        
        return self.session_factory()
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            logger.info("数据库连接已关闭")
            self._engine = None
            self._session_factory = None
            self._initialized = False


# 创建全局数据库管理器实例
db_manager = DatabaseManager()
