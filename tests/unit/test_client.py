import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qzone_mcp.api.client import QzoneClient
from qzone_mcp.api.session import QzoneSession
from qzone_mcp.api.model import QzoneContext
from qzone_mcp.config import AppConfig


class TestQzoneClient:
    def _create_mock_session(self, status=200, json_data=None, text_data=""):
        mock_response = MagicMock()
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=json_data or {})
        mock_response.text = AsyncMock(return_value=text_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        class MockResponseWrapper:
            def __await__(self):
                async def wrapper():
                    return mock_response
                return wrapper().__await__()

            async def __aenter__(self):
                return mock_response

            async def __aexit__(self, *args, **kwargs):
                return None

        mock_session = MagicMock()

        def mock_get(*args, **kwargs):
            return MockResponseWrapper()

        mock_session.get = mock_get
        mock_session.post = mock_get
        mock_session.request = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        return mock_session

    @pytest.mark.asyncio
    async def test_publish_post_params(self):
        config = AppConfig()
        config.onebot.enabled = False
        config.qzone.cookie = "uin=o123456789; skey=test_skey; p_skey=test_p_skey"

        session = QzoneSession(config)
        ctx = await session.login(config.qzone.cookie)

        client = QzoneClient(session)

        mock_session = self._create_mock_session(
            status=200,
            json_data={"code": 0, "tid": "123456"}
        )

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await client.publish_post("test content")

            assert result.success is True
            assert result.tid == "123456"
            assert result.message == "发布成功"

    @pytest.mark.asyncio
    async def test_publish_post_failure(self):
        config = AppConfig()
        config.onebot.enabled = False
        config.qzone.cookie = "uin=o123456789; skey=test_skey; p_skey=test_p_skey"

        session = QzoneSession(config)
        await session.login(config.qzone.cookie)

        client = QzoneClient(session)

        mock_session = self._create_mock_session(
            status=200,
            json_data={"code": -1, "message": "发布失败"}
        )

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await client.publish_post("test content")

            assert result.success is False
            assert result.message == "发布失败"

    @pytest.mark.asyncio
    async def test_like_post(self):
        config = AppConfig()
        config.onebot.enabled = False
        config.qzone.cookie = "uin=o123456789; skey=test_skey; p_skey=test_p_skey"

        session = QzoneSession(config)
        await session.login(config.qzone.cookie)

        client = QzoneClient(session)

        mock_session = self._create_mock_session(
            status=200,
            json_data={"code": 0}
        )

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await client.like_post("123456", 123456789)

            assert result.success is True
            assert result.message == "点赞成功"

    @pytest.mark.asyncio
    async def test_comment_post(self):
        config = AppConfig()
        config.onebot.enabled = False
        config.qzone.cookie = "uin=o123456789; skey=test_skey; p_skey=test_p_skey"

        session = QzoneSession(config)
        await session.login(config.qzone.cookie)

        client = QzoneClient(session)

        mock_session = self._create_mock_session(
            status=200,
            json_data={"code": 0, "commentId": "789012"}
        )

        with patch("aio