from datetime import datetime, timezone
from typing import Optional, List, ClassVar
from pydantic import BaseModel, Field, field_validator, field_serializer


class QzoneConfig(BaseModel):
    cookie: str = Field(default="")
    cookie_expires_at: Optional[datetime] = Field(default=None)
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=2)

    @field_serializer('cookie_expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat()


class OneBotConfig(BaseModel):
    enabled: bool = Field(default=False)
    provider: str = Field(default="napcat")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=3000)
    timeout: int = Field(default=10)
    api_path: str = Field(default="/get_cookies")
    token: str = Field(default="")

    @field_validator('port')
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("端口号必须在1-65535之间")
        return v


class LogConfig(BaseModel):
    level: str = Field(default="INFO")
    max_size: int = Field(default=10485760)
    backup_count: int = Field(default=5)
    console_enabled: bool = Field(default=True)
    file_enabled: bool = Field(default=True)


class MetadataConfig(BaseModel):
    last_login_uin: Optional[str] = Field(default=None)
    auto_refresh_cookie: bool = Field(default=True)


class ConfigSchema(BaseModel):
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    qzone: QzoneConfig = Field(default_factory=QzoneConfig)
    onebot: OneBotConfig = Field(default_factory=OneBotConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)

    SENSITIVE_FIELDS: ClassVar[set] = {
        "qzone.cookie",
        "onebot.token"
    }

    @field_serializer('created_at', 'updated_at')
    def serialize_datetimes(self, value: datetime) -> str:
        return value.isoformat()

    def get_sensitive_field_value(self, field_path: str) -> str:
        parts = field_path.split(".")
        value = self
        for part in parts:
            value = getattr(value, part, "")
        return str(value) if value else ""

    def set_sensitive_field_value(self, field_path: str, value: str) -> None:
        parts = field_path.split(".")
        obj = self
        for i, part in enumerate(parts[:-1]):
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    @classmethod
    def default(cls) -> "ConfigSchema":
        now = datetime.now(timezone.utc)
        return cls(
            version="1.0.0",
            created_at=now,
            updated_at=now,
            qzone=QzoneConfig(),
            onebot=OneBotConfig(),
            log=LogConfig(),
            metadata=MetadataConfig()
        )