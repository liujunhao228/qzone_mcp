import os
from pathlib import Path
from unittest.mock import patch

import pytest

from qzone_mcp.config import AppConfig


def test_config_from_env():
    with patch.dict(os.environ, {
        "QZONE_QZONE__COOKIE": "test_cookie",
        "QZONE_ONEBOT__ENABLED": "true",
        "QZONE_ONEBOT__PROVIDER": "llonebot",
        "QZONE_ONEBOT__HOST": "192.168.1.1",
        "QZONE_ONEBOT__PORT": "5700",
    }):
        config = AppConfig()
        assert config.qzone.cookie == "test_cookie"
        assert config.onebot.enabled is True
        assert config.onebot.provider == "llonebot"
        assert config.onebot.host == "192.168.1.1"
        assert config.onebot.port == 5700


def test_config_defaults():
    config = AppConfig(model_config={"env_file": None})
    assert config.qzone.cookie == ""
    assert config.qzone.timeout == 30
    assert config.onebot.enabled is False
    assert config.onebot.provider == "napcat"
    assert config.onebot.host == "127.0.0.1"
    assert config.onebot.port == 3000
    assert config.onebot.api_path == "/get_cookies"


def test_has_valid_cookie():
    config = AppConfig(model_config={"env_file": None})
    assert config.has_valid_cookie is False
    
    config.qzone.cookie = "uin=o123456; skey=abc123"
    assert config.has_valid_cookie is True


def test_ensure_data_dir(tmp_path):
    config = AppConfig()
    config.data_dir = tmp_path / "test_qzone_data"
    
    assert not config.data_dir.exists()
    config.ensure_data_dir()
    assert config.data_dir.exists()
    assert config.data_dir.is_dir()


def test_onebot_provider_validation():
    config = AppConfig()
    assert config.onebot.provider in ["napcat", "llonebot", "generic"]