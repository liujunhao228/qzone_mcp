import asyncio
import re
from abc import ABC, abstractmethod
from typing import Optional

import aiohttp

from ..config import AppConfig


class CookieProvider(ABC):
    @abstractmethod
    async def fetch_cookies(self, domain: str) -> str:
        pass


class NapcatProvider(CookieProvider):
    def __init__(self, config: AppConfig):
        self.config = config

    async def fetch_cookies(self, domain: str) -> str:
        cfg = self.config.onebot
        url = f"http://{cfg.host}:{cfg.port}{cfg.api_path}"
        
        headers = {}
        if cfg.token:
            headers["Authorization"] = f"Bearer {cfg.token}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cfg.timeout)) as session:
            async with session.get(url, params={"domain": domain}, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"从 napcat 获取 cookie 失败: {resp.status}")
                data = await resp.json()
                cookies_str = data.get("data", {}).get("cookies", "")
                if not cookies_str:
                    raise RuntimeError("napcat 返回的 cookie 为空")
                return cookies_str


class LlOnebotProvider(CookieProvider):
    def __init__(self, config: AppConfig):
        self.config = config

    async def fetch_cookies(self, domain: str) -> str:
        cfg = self.config.onebot
        url = f"http://{cfg.host}:{cfg.port}{cfg.api_path}"
        
        headers = {}
        if cfg.token:
            headers["Authorization"] = f"Bearer {cfg.token}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cfg.timeout)) as session:
            async with session.get(url, params={"domain": domain}, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"从 llonebot 获取 cookie 失败: {resp.status}")
                data = await resp.json()
                cookies_str = data.get("data", {}).get("cookies", "")
                if not cookies_str:
                    raise RuntimeError("llonebot 返回的 cookie 为空")
                return cookies_str


def create_provider(config: AppConfig) -> CookieProvider:
    provider_type = config.onebot.provider.lower()
    if provider_type == "napcat":
        return NapcatProvider(config)
    elif provider_type == "llonebot":
        return LlOnebotProvider(config)
    else:
        raise ValueError(f"不支持的 provider 类型: {provider_type}")
