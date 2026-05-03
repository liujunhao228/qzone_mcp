from pathlib import Path
from typing import Optional, List, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .config_manager import default_manager


class OneBotConfig(BaseModel):
    enabled: bool = Field(default=False, description="是否启用 OneBot 客户端自动获取 cookie")
    provider: Literal["napcat", "llonebot", "generic"] = Field(
        default="napcat", 
        description="OneBot 客户端类型: napcat, llonebot, generic"
    )
    host: str = Field(default="127.0.0.1", description="OneBot 服务地址")
    port: int = Field(default=3000, description="OneBot HTTP API 端口")
    timeout: int = Field(default=10, description="请求超时时间(秒)")
    api_path: str = Field(default="/get_cookies", description="获取 cookie 的 API 路径")
    token: Optional[str] = Field(default=None, description="Bearer token，用于身份验证")


class QzoneConfig(BaseModel):
    cookie: str = Field(default="", description="QQ空间 Cookie 字符串")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=2, description="重试延迟(秒)")


class LogConfig(BaseModel):
    level: str = Field(default="INFO", description="日志级别: DEBUG/INFO/WARN/ERROR/FATAL")
    path: Path = Field(default=Path.home() / ".qzone" / "logs", description="日志存储目录")
    max_size: int = Field(default=10485760, description="单文件最大字节数(默认10MB)")
    backup_count: int = Field(default=5, description="保留的日志备份数")
    console_enabled: bool = Field(default=True, description="是否输出到控制台")
    file_enabled: bool = Field(default=True, description="是否输出到文件")


class AppConfig(BaseSettings):
    qzone: QzoneConfig = QzoneConfig()
    onebot: OneBotConfig = OneBotConfig()
    log: LogConfig = LogConfig()
    data_dir: Path = Field(
        default=Path.home() / ".qzone",
        description="数据存储目录"
    )
    admins: List[str] = Field(default=[], description="管理员 QQ 号列表")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_prefix="QZONE_",
        extra="ignore"
    )

    @property
    def has_valid_cookie(self) -> bool:
        return bool(self.qzone.cookie.strip())

    def ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_from_config_manager(self) -> None:
        cfg = default_manager.load()
        self.qzone.cookie = cfg.qzone.cookie
        self.qzone.timeout = cfg.qzone.timeout
        self.qzone.max_retries = cfg.qzone.max_retries
        self.qzone.retry_delay = cfg.qzone.retry_delay
        self.onebot.enabled = cfg.onebot.enabled
        self.onebot.provider = cfg.onebot.provider
        self.onebot.host = cfg.onebot.host
        self.onebot.port = cfg.onebot.port
        self.onebot.timeout = cfg.onebot.timeout
        self.onebot.api_path = cfg.onebot.api_path
        self.onebot.token = cfg.onebot.token if cfg.onebot.token else None
        self.log.level = cfg.log.level
        self.log.max_size = cfg.log.max_size
        self.log.backup_count = cfg.log.backup_count
        self.log.console_enabled = cfg.log.console_enabled
        self.log.file_enabled = cfg.log.file_enabled


config = AppConfig()
config.load_from_config_manager()