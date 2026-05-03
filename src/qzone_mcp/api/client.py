import asyncio
import logging
from typing import Any, Optional

import aiohttp

from ..config import AppConfig
from ..session import QzoneSession, LoginExpiredError
from ..parser import QzoneJsonParser
from .constants import (
    HTTP_STATUS_UNAUTHORIZED,
    HTTP_STATUS_FORBIDDEN,
    QZONE_CODE_LOGIN_EXPIRED,
    QZONE_CODE_UNKNOWN,
    QZONE_MSG_PERMISSION_DENIED,
    QZONE_INTERNAL_META_KEY,
    QZONE_INTERNAL_HTTP_STATUS_KEY,
)

logger = logging.getLogger(__name__)


class QzoneHttpClient:
    def __init__(self, session: QzoneSession, config: AppConfig):
        self.session = session
        self.config = config
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_http_session(self) -> aiohttp.ClientSession:
        if not self._http_session:
            timeout = aiohttp.ClientTimeout(total=self.config.qzone.timeout)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

    async def close(self):
        if self._http_session:
            await self._http_session.close()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        retry: int = 0,
    ) -> dict[str, Any]:
        ctx = await self.session.get_ctx()
        http_session = await self._get_http_session()

        kwargs: dict[str, Any] = {
            "params": params or {},
        }
        if data:
            kwargs["data"] = data
        kwargs.setdefault("headers", {})
        kwargs["headers"].update(ctx.headers())
        kwargs["cookies"] = ctx.cookies()

        try:
            async with http_session.request(method, url, timeout=timeout, **kwargs) as resp:
                text = await resp.text()

            parsed = QzoneJsonParser.parse_response(text)
            meta = parsed.get(QZONE_INTERNAL_META_KEY)
            if not isinstance(meta, dict):
                meta = {}
                parsed[QZONE_INTERNAL_META_KEY] = meta
            meta[QZONE_INTERNAL_HTTP_STATUS_KEY] = resp.status

            if resp.status == HTTP_STATUS_UNAUTHORIZED or parsed.get("code") == QZONE_CODE_LOGIN_EXPIRED:
                if retry >= self.config.qzone.max_retries:
                    raise RuntimeError("登录失效，重试失败")

                logger.warning("登录失效，重新登录中")
                await self.session.invalidate()
                await self.session.login()
                return await self.request(
                    method, url, params=params, data=data, headers=headers, retry=retry + 1
                )

            if resp.status == HTTP_STATUS_FORBIDDEN and parsed.get("code") in (QZONE_CODE_UNKNOWN, None):
                parsed["code"] = resp.status
                parsed["message"] = QZONE_MSG_PERMISSION_DENIED

            return parsed

        except LoginExpiredError:
            if retry >= self.config.qzone.max_retries:
                raise
            await self.session.invalidate()
            await asyncio.sleep(self.config.qzone.retry_delay * (retry + 1))
            return await self.request(method, url, params=params, data=data, headers=headers, retry=retry + 1)
        except aiohttp.ClientError as e:
            if retry >= self.config.qzone.max_retries:
                raise
            await asyncio.sleep(self.config.qzone.retry_delay * (retry + 1))
            return await self.request(method, url, params=params, data=data, headers=headers, retry=retry + 1)
