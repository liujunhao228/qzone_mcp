import asyncio
import re
from typing import Optional

import aiohttp

from ..config import config, AppConfig
from .model import QzoneContext


class LoginExpiredError(Exception):
    pass


class CookieParseError(Exception):
    pass


class QzoneSession:
    DOMAIN = "user.qzone.qq.com"

    def __init__(self, cfg: AppConfig = config):
        self.cfg = cfg
        self._ctx: Optional[QzoneContext] = None
        self._lock = asyncio.Lock()

    async def get_ctx(self) -> QzoneContext:
        async with self._lock:
            if not self._ctx:
                await self.login()
            return self._ctx

    async def login(self, cookies_str: Optional[str] = None) -> QzoneContext:
        if cookies_str:
            ctx = await self._parse_cookies(cookies_str)
        elif self.cfg.onebot.enabled:
            cookies_str = await self._fetch_from_onebot()
            ctx = await self._parse_cookies(cookies_str)
            self.cfg.qzone.cookie = cookies_str
        elif self.cfg.has_valid_cookie:
            ctx = await self._parse_cookies(self.cfg.qzone.cookie)
        else:
            raise ValueError("未配置 Cookie 且未启用 OneBot 客户端")

        self._ctx = ctx
        return ctx

    async def invalidate(self) -> None:
        self._ctx = None

    async def _fetch_from_onebot(self) -> str:
        cfg = self.cfg.onebot
        url = f"http://{cfg.host}:{cfg.port}{cfg.api_path}"
        
        params = {"domain": self.DOMAIN}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cfg.timeout)) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"从 {cfg.provider} 获取 cookie 失败: {resp.status}")
                data = await resp.json()
                
                if cfg.provider == "napcat":
                    cookies_str = data.get("data", {}).get("cookies", "")
                elif cfg.provider == "llonebot":
                    cookies_str = data.get("cookies", "")
                else:
                    cookies_str = data.get("cookies", "") or data.get("data", "")
                
                if not cookies_str:
                    raise RuntimeError(f"{cfg.provider} 返回的 cookie 为空")
                return cookies_str

    async def _parse_cookies(self, cookies_str: str) -> QzoneContext:
        uin_match = re.search(r'(?:^|;)\s*uin=o?(\d+)', cookies_str)
        skey_match = re.search(r'(?:^|;)\s*skey=([^;]+)', cookies_str)
        p_skey_match = re.search(r'(?:^|;)\s*p_skey=([^;]+)', cookies_str)

        if not uin_match or not skey_match or not p_skey_match:
            raise CookieParseError("无法从 Cookie 中解析必要字段")

        return QzoneContext(
            uin=int(uin_match.group(1)),
            skey=skey_match.group(1),
            p_skey=p_skey_match.group(1),
            cookies_str=cookies_str
        )

    @property
    def is_logged_in(self) -> bool:
        return self._ctx is not None