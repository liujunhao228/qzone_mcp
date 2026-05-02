import logging
from typing import Optional

from logging.handlers import RotatingFileHandler

from ..config import config
from .context import get_request_id
from .formatters import CustomLogFormatter, ColoredLogFormatter


class QzoneLogger(logging.Logger):
    """自定义日志类，支持请求ID上下文"""
    
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
        if extra is None:
            extra = {}
        extra.setdefault('request_id', get_request_id())
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """记录异常信息，包含完整堆栈"""
        extra = kwargs.pop('extra', {})
        extra.setdefault('request_id', get_request_id())
        super().exception(msg, *args, exc_info=exc_info, extra=extra, **kwargs)


def init_logging() -> None:
    """初始化日志系统"""
    log_config = config.log
    
    logging.setLoggerClass(QzoneLogger)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config.level)
    
    root_logger.handlers.clear()
    
    if log_config.console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_config.level)
        console_handler.setFormatter(ColoredLogFormatter())
        root_logger.addHandler(console_handler)
    
    if log_config.file_enabled:
        log_path = log_config.path
        try:
            log_path.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                filename=log_path / "qzone-mcp.log",
                maxBytes=log_config.max_size,
                backupCount=log_config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_config.level)
            file_handler.setFormatter(CustomLogFormatter())
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"无法创建日志目录: {e}")


def get_logger(name: str) -> logging.Logger:
    """获取配置好的日志器"""
    return logging.getLogger(name)