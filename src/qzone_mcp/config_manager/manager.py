import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from .schema import ConfigSchema
from .crypto import CryptoManager


class ConfigManager:
    _CONFIG_FILE_NAME = "config.json"
    _CURRENT_VERSION = "1.0.0"

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = self._get_default_data_dir()
        
        self.data_dir = data_dir
        self.config_path = data_dir / self._CONFIG_FILE_NAME
        
        try:
            self.crypto = CryptoManager(data_dir)
        except PermissionError:
            raise RuntimeError(f"无法访问配置目录 {data_dir}，请检查权限")
        
        self._config: Optional[ConfigSchema] = None

    def _get_default_data_dir(self) -> Path:
        env_path = os.environ.get("QZONE_CONFIG_DIR")
        if env_path:
            path = Path(env_path)
            path.mkdir(parents=True, exist_ok=True)
            return path
        
        candidates = [
            Path(__file__).parent.parent.parent / ".qzone",
            Path.cwd() / ".qzone",
            Path.home() / ".qzone",
        ]
        
        for candidate in candidates:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                test_file = candidate / ".test_write"
                test_file.touch()
                test_file.unlink()
                return candidate
            except (PermissionError, FileNotFoundError, OSError):
                continue
        
        raise RuntimeError("无法找到可写的配置目录，请设置 QZONE_CONFIG_DIR 环境变量")

    def load(self) -> ConfigSchema:
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data = self._migrate(data)
                data = self._decrypt_sensitive_fields(data)
                self._config = ConfigSchema(**data)
            except Exception as e:
                raise RuntimeError(f"加载配置文件失败: {e}")
        else:
            self._config = ConfigSchema.default()
            self.save()

        return self._config

    def save(self, config: Optional[ConfigSchema] = None) -> None:
        if config is None:
            if self._config is None:
                self._config = ConfigSchema.default()
            config = self._config

        config.updated_at = datetime.now(timezone.utc)
        data = json.loads(config.model_dump_json())
        data = self._encrypt_sensitive_fields(data)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.config_path.chmod(0o600)

        self._config = config

    def _encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for field in ConfigSchema.SENSITIVE_FIELDS:
            parts = field.split(".")
            obj = data
            for i, part in enumerate(parts[:-1]):
                if part not in obj:
                    break
                obj = obj[part]
            else:
                if parts[-1] in obj and obj[parts[-1]]:
                    obj[parts[-1]] = self.crypto.encrypt(obj[parts[-1]])
        return data

    def _decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for field in ConfigSchema.SENSITIVE_FIELDS:
            parts = field.split(".")
            obj = data
            for i, part in enumerate(parts[:-1]):
                if part not in obj:
                    break
                obj = obj[part]
            else:
                if parts[-1] in obj and obj[parts[-1]]:
                    obj[parts[-1]] = self.crypto.decrypt(obj[parts[-1]])
        return data

    def _migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        version = data.get("version", "0.0.0")
        
        if version == "0.0.0":
            data = self._migrate_from_v0_to_v1(data)
        
        data["version"] = self._CURRENT_VERSION
        return data

    def _migrate_from_v0_to_v1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        migrated = {
            "version": "1.0.0",
            "created_at": now,
            "updated_at": now,
            "qzone": {
                "cookie": data.get("cookie", ""),
                "cookie_expires_at": None,
                "timeout": data.get("timeout", 30),
                "max_retries": data.get("max_retries", 3),
                "retry_delay": data.get("retry_delay", 2)
            },
            "onebot": {
                "enabled": data.get("onebot_enabled", False),
                "provider": data.get("onebot_provider", "napcat"),
                "host": data.get("onebot_host", "127.0.0.1"),
                "port": data.get("onebot_port", 3000),
                "timeout": data.get("onebot_timeout", 10),
                "api_path": data.get("onebot_api_path", "/get_cookies"),
                "token": data.get("onebot_token", "")
            },
            "log": {
                "level": data.get("log_level", "INFO"),
                "max_size": data.get("log_max_size", 10485760),
                "backup_count": data.get("log_backup_count", 5),
                "console_enabled": data.get("log_console_enabled", True),
                "file_enabled": data.get("log_file_enabled", True)
            },
            "metadata": {
                "last_login_uin": None,
                "auto_refresh_cookie": True
            }
        }
        return migrated

    def get(self, key: str) -> Any:
        config = self.load()
        parts = key.split(".")
        value = config
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        return value

    def set(self, key: str, value: Any) -> None:
        config = self.load()
        parts = key.split(".")
        obj = config
        for i, part in enumerate(parts[:-1]):
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
        self.save(config)

    def reset(self, key: Optional[str] = None) -> None:
        if key is None:
            self._config = ConfigSchema.default()
        else:
            config = self.load()
            default_config = ConfigSchema.default()
            parts = key.split(".")
            obj, default_obj = config, default_config
            for i, part in enumerate(parts[:-1]):
                obj = getattr(obj, part)
                default_obj = getattr(default_obj, part)
            setattr(obj, parts[-1], getattr(default_obj, parts[-1]))
        self.save()

    def export(self, export_path: Path) -> None:
        config = self.load()
        data = json.loads(config.model_dump_json())
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_config(self, import_path: Path) -> None:
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = self._migrate(data)
        data = self._decrypt_sensitive_fields(data)
        self._config = ConfigSchema(**data)
        self.save()

    @property
    def config(self) -> ConfigSchema:
        return self.load()