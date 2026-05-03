import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, Callable

from ..config import config, AppConfig
from ..model import QzoneContext
from .provider import create_provider
from ..config_manager import default_manager


class LoginExpiredError(Exception):
    pass


class CookieParseError(Exception):
    pass


class QzoneSession:
    DOMAIN = "user.qzone.qq.com"
    COOKIE_EXPIRE_THRESHOLD = timedelta(hours=1)

    def __init__(self, cfg: AppConfig = config):
        self.cfg = cfg
        self._ctx: Optional[QzoneContext] = None
        self._lock = asyncio.Lock()
        self._provider = create_provider(cfg) if cfg.onebot.enabled else None
        self._config_manager = default_manager
        self._cookie_update_callback: Optional[Callable[[str], None]] = None

    def set_cookie_update_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置Cookie更新回调函数
        """
        self._cookie_update_callback = callback

    async def get_ctx(self) -> QzoneContext:
        async with self._lock:
            if not self._ctx or await self._is_cookie_expired():
                await self.login()
            return self._ctx

    async def login(self, cookies_str: Optional[str] = None) -> QzoneContext:
        if cookies_str:
            ctx = await self._parse_cookies(cookies_str)
            await self._update_cookie_config(cookies_str)
        elif self.cfg.onebot.enabled and self._provider:
            cookies_str = await self._provider.fetch_cookies(self.DOMAIN)
            ctx = await self._parse_cookies(cookies_str)
            await self._update_cookie_config(cookies_str)
        elif self.cfg.has_valid_cookie:
            ctx = await self._parse_cookies(self.cfg.qzone.cookie)
            if await self._is_cookie_expired() and self.cfg.onebot.enabled and self._provider:
                cookies_str = await self._provider.fetch_cookies(self.DOMAIN)
                ctx = await self._parse_cookies(cookies_str)
                await self._update_cookie_config(cookies_str)
        else:
            raise ValueError("未配置 Cookie 且未启用 OneBot 客户端")

        self._ctx = ctx
        return ctx

    async def invalidate(self) -> None:
        """
        登出，清除会话信息和Cookie配置
        """
        self._ctx = None
        await self._clear_cookie_config()

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

    async def _is_cookie_expired(self) -> bool:
        """
        检查Cookie是否过期
        """
        config = self._config_manager.load()
        expires_at = config.qzone.cookie_expires_at
        
        if expires_at is None:
            return False
        
        now = datetime.utcnow()
        return now + self.COOKIE_EXPIRE_THRESHOLD >= expires_at

    async def _update_cookie_config(self, cookies_str: str) -> None:
        """
        更新Cookie配置，包括过期时间
        """
        config = self._config_manager.load()
        config.qzone.cookie = cookies_str
        
        expires_at = self._extract_expire_time(cookies_str)
        config.qzone.cookie_expires_at = expires_at
        
        if config.metadata.last_login_uin is None:
            uin_match = re.search(r'(?:^|;)\s*uin=o?(\d+)', cookies_str)
            if uin_match:
                config.metadata.last_login_uin = uin_match.group(1)
        
        self._config_manager.save(config)
        
        if self._cookie_update_callback:
            self._cookie_update_callback(cookies_str)

    async def _clear_cookie_config(self) -> None:
        """
        清除Cookie配置
        """
        config = self._config_manager.load()
        config.qzone.cookie = ""
        config.qzone.cookie_expires_at = None
        self._config_manager.save(config)

    def _extract_expire_time(self, cookies_str: str) -> Optional[datetime]:
        """
        从Cookie字符串中提取过期时间
        
        Cookie中的expires字段格式通常为: expires=Thu, 01 Jan 1970 00:00:00 GMT
        """
        expire_match = re.search(r'(?:^|;)\s*expires=([^;]+)', cookies_str, re.IGNORECASE)
        if not expire_match:
            return None
        
        expire_str = expire_match.group(1).strip()
        try:
            return datetime.strptime(expire_str, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            try:
                return datetime.strptime(expire_str, '%a, %d-%b-%Y %H:%M:%S %Z')
            except ValueError:
                return None

    async def refresh_cookie(self) -> bool:
        """
        手动刷新Cookie
        
        Returns:
            是否成功刷新
        """
        if not self.cfg.onebot.enabled or not self._provider:
            return False
        
        try:
            cookies_str = await self._provider.fetch_cookies(self.DOMAIN)
            ctx = await self._parse_cookies(cookies_str)
            await self._update_cookie_config(cookies_str)
            self._ctx = ctx
            return True
        except Exception:
            return False

    @property
    def is_logged_in(self) -> bool:
        return self._ctx is not None

    @property
    def cookie_expires_at(self) -> Optional[datetime]:
        """
        获取Cookie过期时间
        """
        config = self._config_manager.load()
        return config.qzone.cookie_expires_at

    async def check_and_refresh_cookie(self) -> bool:
        """
        检查并自动刷新过期的Cookie
        
        Returns:
            是否执行了刷新操作
        """
        if await self._is_cookie_expired() and self.cfg.onebot.enabled and self._provider:
            return await self.refresh_cookie()
        return False