import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from qzone_mcp.api.session import QzoneSession, LoginExpiredError, CookieParseError
from qzone_mcp.config import AppConfig


class TestLLOneBotIntegration:
    def _create_mock_session(self, status=200, cookies=""):
        """Helper to create a mock aiohttp session with proper async context manager support."""
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.json = AsyncMock(return_value={"cookies": cookies})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        return mock_session

    @pytest.mark.asyncio
    async def test_fetch_cookie_from_llonebot_success(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        config.onebot.api_path = "/get_cookies"
        
        session = QzoneSession(config)
        
        mock_cookies = "uin=o123456789; skey=abcdefg123456; p_skey=xyz7890"
        mock_session = self._create_mock_session(status=200, cookies=mock_cookies)
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            cookies_str = await session._fetch_from_onebot()
            assert cookies_str == mock_cookies

    @pytest.mark.asyncio
    async def test_fetch_cookie_from_llonebot_http_error(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        
        session = QzoneSession(config)
        
        mock_session = self._create_mock_session(status=500)
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(RuntimeError, match="获取 cookie 失败"):
                await session._fetch_from_onebot()

    @pytest.mark.asyncio
    async def test_fetch_cookie_from_llonebot_empty_response(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        
        session = QzoneSession(config)
        
        mock_session = self._create_mock_session(status=200, cookies="")
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(RuntimeError, match="返回的 cookie 为空"):
                await session._fetch_from_onebot()

    @pytest.mark.asyncio
    async def test_login_via_llonebot(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        
        session = QzoneSession(config)
        
        mock_cookies = "uin=o987654321; skey=test_skey; p_skey=test_p_skey"
        mock_session = self._create_mock_session(status=200, cookies=mock_cookies)
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            ctx = await session.login()
            
            assert ctx.uin == 987654321
            assert ctx.skey == "test_skey"
            assert ctx.p_skey == "test_p_skey"
            assert session.is_logged_in is True
            assert config.qzone.cookie == mock_cookies

    @pytest.mark.asyncio
    async def test_login_via_llonebot_invalid_cookie(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        
        session = QzoneSession(config)
        
        mock_session = self._create_mock_session(status=200, cookies="invalid=cookie")
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(CookieParseError):
                await session.login()

    @pytest.mark.asyncio
    async def test_llonebot_timeout(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        config.onebot.timeout = 1
        
        session = QzoneSession(config)
        
        mock_session = AsyncMock()
        
        async def slow_get(*args, **kwargs):
            await asyncio.sleep(2)
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"cookies": "test"})
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            return mock_response
        
        mock_session.get = slow_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(asyncio.TimeoutError):
                await session._fetch_from_onebot()

    @pytest.mark.asyncio
    async def test_get_ctx_auto_login_via_llonebot(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        
        session = QzoneSession(config)
        
        mock_cookies = "uin=o1122334455; skey=auto_login_key; p_skey=auto_login_pkey"
        mock_session = self._create_mock_session(status=200, cookies=mock_cookies)
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            ctx = await session.get_ctx()
            
            assert ctx.uin == 1122334455
            assert ctx.skey == "auto_login_key"
            assert session.is_logged_in is True

    @pytest.mark.asyncio
    async def test_llonebot_provider_response_format(self):
        config = AppConfig()
        config.onebot.enabled = True
        config.onebot.provider = "llonebot"
        config.onebot.host = "127.0.0.1"
        config.onebot.port = 5700
        
        session = QzoneSession(config)
        
        llonebot_response = {
            "status": "success",
            "cookies": "uin=o123456789; skey=abc123; p_skey=xyz789",
            "message": "success"
        }
        
        mock_session = self._create_mock_session(status=200)
        mock_session.get = AsyncMock(return_value=AsyncMock(
            status=200,
            json=AsyncMock(return_value=llonebot_response),
            __aenter__=AsyncMock(return_value=AsyncMock(
                status=200,
                json=AsyncMock(return_value=llonebot_response)
            )),
            __aexit__=AsyncMock(return_value=None)
        ))
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            cookies_str = await session._fetch_from_onebot()
            assert cookies_str == llonebot_response["cookies"]