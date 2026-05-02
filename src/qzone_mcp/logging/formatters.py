import logging
import time
from typing import Optional

from .context import get_request_id


class CustomLogFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    LOG_FORMAT = "[%(asctime)s] [%(levelname)-5s] [%(module)s] [%(request_id)s] - %(message)s"
    
    def __init__(self):
        super().__init__(fmt=self.LOG_FORMAT)
    
    def formatTime(self, record: logging.LogRecord, datefmt=None):
        """自定义时间格式化，支持毫秒级精度"""
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            s += f".{int(record.created * 1000) % 1000:03d}"
        return s
    
    def format(self, record: logging.LogRecord) -> str:
        record.request_id = getattr(record, 'request_id', get_request_id())
        record.module = record.name.split('.')[-1] if record.name else 'root'
        return super().format(record)


class ColoredLogFormatter(CustomLogFormatter):
    """带颜色的日志格式化器（仅用于控制台输出）"""
    
    COLOR_CODES = {
        'DEBUG': '\033[94m',      # 蓝色
        'INFO': '\033[92m',       # 绿色
        'WARNING': '\033[93m',    # 黄色
        'ERROR': '\033[91m',      # 红色
        'CRITICAL': '\033[95m',   # 紫色
    }
    RESET_CODE = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        level_name = record.levelname
        color_code = self.COLOR_CODES.get(level_name, '')
        record.levelname = f"{color_code}{level_name}{self.RESET_CODE}"
        return super().format(record)