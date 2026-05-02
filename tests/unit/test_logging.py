import logging
import os
import re
import tempfile
from pathlib import Path

import pytest

from qzone_mcp.config import config, LogConfig
from qzone_mcp.logging import get_logger, init_logging, set_request_id


class TestLoggingConfiguration:
    """测试日志配置"""
    
    def test_log_config_defaults(self):
        """测试日志配置默认值"""
        log_config = LogConfig()
        assert log_config.level == "INFO"
        assert log_config.max_size == 10485760
        assert log_config.backup_count == 5
        assert log_config.console_enabled is True
        assert log_config.file_enabled is True
    
    def test_log_config_custom(self):
        """测试自定义日志配置"""
        log_config = LogConfig(
            level="DEBUG",
            max_size=5242880,
            backup_count=10,
            console_enabled=False,
            file_enabled=True
        )
        assert log_config.level == "DEBUG"
        assert log_config.max_size == 5242880
        assert log_config.backup_count == 10
        assert log_config.console_enabled is False
        assert log_config.file_enabled is True


class TestLoggerCreation:
    """测试日志器创建"""
    
    def test_get_logger(self):
        """测试获取日志器"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_logger_levels(self):
        """测试日志级别"""
        logger = get_logger("level_test")
        logger.setLevel(logging.DEBUG)
        
        assert logger.isEnabledFor(logging.DEBUG)
        assert logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.WARNING)
        assert logger.isEnabledFor(logging.ERROR)
        assert logger.isEnabledFor(logging.CRITICAL)


class TestLogFormat:
    """测试日志格式"""
    
    def test_log_format_structure(self):
        """测试日志格式结构"""
        import io
        from qzone_mcp.logging.formatters import CustomLogFormatter
        
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(CustomLogFormatter())
        handler.setLevel(logging.DEBUG)
        
        logger = get_logger("format_test")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.propagate = False
        
        logger.info("test message")
        
        log_output = stream.getvalue()
        
        pattern = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+\] \[INFO \] \[format_test\] \[N/A\] - test message"
        assert re.match(pattern, log_output.strip()), f"日志格式不匹配: {log_output}"
        
        logger.removeHandler(handler)
        logger.propagate = True
    
    def test_request_id_in_log(self):
        """测试请求ID在日志中的记录"""
        import io
        from qzone_mcp.logging.formatters import CustomLogFormatter
        
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(CustomLogFormatter())
        handler.setLevel(logging.DEBUG)
        
        logger = get_logger("request_id_test")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.propagate = False
        
        set_request_id("req-test123")
        logger.info("test with request id")
        
        log_output = stream.getvalue()
        
        assert "[req-test123]" in log_output, f"请求ID未在日志中找到: {log_output}"
        
        logger.removeHandler(handler)
        logger.propagate = True


class TestLogRotation:
    """测试日志轮转"""
    
    def test_log_file_creation(self, tmp_path):
        """测试日志文件创建"""
        original_log_path = config.log.path
        original_file_enabled = config.log.file_enabled
        original_level = config.log.level
        
        try:
            config.log.path = tmp_path / "logs"
            config.log.file_enabled = True
            config.log.level = "DEBUG"
            
            init_logging()
            
            logger = get_logger("file_test")
            logger.info("test log message")
            
            log_file = config.log.path / "qzone-mcp.log"
            assert log_file.exists(), f"日志文件未创建: {log_file}"
            
            content = log_file.read_text(encoding='utf-8')
            assert "test log message" in content
        finally:
            config.log.path = original_log_path
            config.log.file_enabled = original_file_enabled
            config.log.level = original_level
            try:
                init_logging()
            except Exception:
                pass


class TestExceptionLogging:
    """测试异常日志记录"""
    
    def test_exception_logging(self):
        """测试异常堆栈记录"""
        import io
        from qzone_mcp.logging.formatters import CustomLogFormatter
        
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(CustomLogFormatter())
        
        logger = get_logger("exception_test")
        logger.addHandler(handler)
        logger.propagate = False
        
        try:
            raise ValueError("test exception")
        except ValueError:
            logger.exception("an error occurred")
        
        log_output = stream.getvalue()
        
        assert "an error occurred" in log_output
        assert "ValueError" in log_output
        assert "test exception" in log_output
        assert "Traceback" in log_output
        
        logger.removeHandler(handler)
        logger.propagate = True


class TestRequestIdContext:
    """测试请求ID上下文管理"""
    
    def test_set_request_id_auto_generate(self):
        """测试自动生成请求ID"""
        request_id = set_request_id()
        assert request_id.startswith("req-")
        assert len(request_id) == 12  # req- + 8 hex chars
    
    def test_set_request_id_custom(self):
        """测试设置自定义请求ID"""
        custom_id = "custom-request-id"
        result = set_request_id(custom_id)
        assert result == custom_id


class TestLogLevelFiltering:
    """测试日志级别过滤"""
    
    def test_debug_level_filter(self):
        """测试DEBUG级别过滤"""
        import io
        from qzone_mcp.logging.formatters import CustomLogFormatter
        
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(CustomLogFormatter())
        handler.setLevel(logging.INFO)
        
        logger = get_logger("filter_test")
        logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        
        logger.debug("debug message")
        logger.info("info message")
        
        log_output = stream.getvalue()
        
        assert "debug message" not in log_output
        assert "info message" in log_output
        
        logger.removeHandler(handler)
        logger.propagate = True