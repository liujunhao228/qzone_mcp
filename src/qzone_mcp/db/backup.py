import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..config import config
from ..logging import get_logger
from .manager import db_manager

logger = get_logger(__name__)


class BackupManager:
    """数据库备份管理器 - 负责数据库备份和恢复操作"""
    
    _instance: Optional['BackupManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self._backup_interval = 24 * 60 * 60  # 24小时
        self._max_backups = 7  # 保留最近7份备份
        self._backup_dir = config.data_dir / "backups"
        self._backup_task = None
        self._running = False
    
    @property
    def backup_dir(self) -> Path:
        """获取备份目录"""
        return self._backup_dir
    
    @property
    def is_running(self) -> bool:
        """检查备份任务是否运行中"""
        return self._running
    
    def ensure_backup_dir(self) -> None:
        """确保备份目录存在"""
        self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_backup_filename(self) -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"qzone_backup_{timestamp}.db"
    
    def get_backup_path(self, filename: Optional[str] = None) -> Path:
        """获取备份文件路径"""
        if filename is None:
            filename = self.get_backup_filename()
        return self._backup_dir / filename
    
    async def backup(self) -> bool:
        """执行数据库备份"""
        try:
            self.ensure_backup_dir()
            
            db_path = config.data_dir / "qzone.db"
            if not db_path.exists():
                logger.warning("数据库文件不存在，跳过备份")
                return False
            
            backup_path = self.get_backup_path()
            
            # 确保数据库连接已关闭或使用在线备份方式
            # SQLite支持在线备份API
            await self._perform_online_backup(backup_path)
            
            logger.info(f"数据库备份成功: {backup_path}")
            
            # 清理过期备份
            await self._cleanup_old_backups()
            
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False
    
    async def _perform_online_backup(self, backup_path: Path) -> None:
        """执行SQLite在线备份"""
        # 使用SQLite的在线备份API
        from sqlalchemy import text
        
        engine = db_manager.engine
        async with engine.connect() as conn:
            # 使用ATTACH DATABASE进行备份
            backup_path_str = str(backup_path).replace("\\", "/")
            await conn.execute(text(f"ATTACH DATABASE '{backup_path_str}' AS backup_db"))
            
            # 获取所有表
            result = await conn.execute(text("SELECT name FROM main.sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            # 复制所有表
            for table in tables:
                await conn.execute(text(f"CREATE TABLE backup_db.{table} AS SELECT * FROM main.{table}"))
            
            await conn.execute(text("DETACH DATABASE backup_db"))
            await conn.commit()
    
    async def _cleanup_old_backups(self) -> None:
        """清理过期备份，保留最近N份"""
        try:
            backup_files = sorted(
                self._backup_dir.glob("qzone_backup_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if len(backup_files) > self._max_backups:
                old_backups = backup_files[self._max_backups:]
                for backup in old_backups:
                    backup.unlink()
                    logger.info(f"已删除过期备份: {backup}")
        except Exception as e:
            logger.error(f"清理过期备份失败: {e}")
    
    async def restore(self, backup_filename: str) -> bool:
        """从备份文件恢复数据库"""
        try:
            backup_path = self._backup_dir / backup_filename
            if not backup_path.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            db_path = config.data_dir / "qzone.db"
            
            # 先关闭数据库连接
            await db_manager.close()
            
            # 复制备份文件到数据库路径
            shutil.copy(str(backup_path), str(db_path))
            
            # 重新初始化数据库
            await db_manager.initialize()
            
            logger.info(f"数据库恢复成功: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return False
    
    def list_backups(self) -> List[dict]:
        """获取备份文件列表"""
        backups = []
        
        if not self._backup_dir.exists():
            return backups
        
        backup_files = sorted(
            self._backup_dir.glob("qzone_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for backup in backup_files:
            stats = backup.stat()
            backups.append({
                "filename": backup.name,
                "path": str(backup),
                "size": stats.st_size,
                "created_at": datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
        
        return backups
    
    def get_latest_backup(self) -> Optional[str]:
        """获取最新备份文件名"""
        backups = self.list_backups()
        return backups[0]["filename"] if backups else None
    
    async def start_scheduled_backup(self) -> None:
        """启动定时备份任务"""
        if self._running:
            return
        
        self._running = True
        logger.info("定时备份任务已启动")
        
        async def backup_loop():
            while self._running:
                await self.backup()
                await asyncio.sleep(self._backup_interval)
        
        self._backup_task = asyncio.create_task(backup_loop())
    
    async def stop_scheduled_backup(self) -> None:
        """停止定时备份任务"""
        self._running = False
        if self._backup_task:
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass
        logger.info("定时备份任务已停止")


# 创建全局备份管理器实例
backup_manager = BackupManager()