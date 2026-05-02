from pathlib import Path
from typing import Optional, List, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    provider: str = Field(default="mock", description="LLM 提供商: openai, mock")
    api_key: str = Field(default="", description="LLM API Key")
    model: str = Field(default="gpt-4o", description="LLM 模型名称")
    api_base: Optional[str] = Field(default=None, description="自定义 API 地址")
    comment_prompt: str = Field(
        default="请针对以下说说内容生成一条合适的评论，语气友好自然，字数在50-200字之间：\n{content}",
        description="生成评论的提示词"
    )
    post_prompt: str = Field(
        default="请根据以下主题生成一条有趣的说说，语气轻松活泼，适合在QQ空间发布：\n{topic}",
        description="生成说说的提示词"
    )


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


class QzoneConfig(BaseModel):
    cookie: str = Field(default="", description="QQ空间 Cookie 字符串")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=2, description="重试延迟(秒)")


class LogConfig(BaseModel):
    level: str = Field(default="DEBUG", description="日志级别: DEBUG/INFO/WARN/ERROR/FATAL")
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


config = AppConfig()