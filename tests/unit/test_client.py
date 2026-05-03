import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qzone_mcp.api.legacy_api import QzoneClient, PublishResult
from qzone_mcp.session import QzoneSession
from qzone_mcp.model import QzoneContext, ApiResponse
from qzone_mcp.config import AppConfig


class TestQzoneClient:
    @pytest.mark.asyncio
    async def test_publish_post_params(self):
        config = AppConfig()
        config.onebot.enabled = False
        config.qzone.cookie = "uin=o123456789; skey=test_skey; p_skey=test_p_skey"

        session = QzoneSession(config)
        await session.login(config.qzone.cookie)

        client = QzoneClient(session)

        mock_api = MagicMock()
        mock_api.publish = AsyncMock(return_value=ApiResponse(
            ok=True, code=0, data={"tid": "123456"}, raw={"code": 0, "tid": "123456"}
        ))
        client._api = mock_api

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

        mock_api = MagicMock()
        mock_api.publish = AsyncMock(return_value=ApiResponse(
            ok=False, code=-1, message="发布失败", raw={"code": -1, "message": "发布失败"}
        ))
        client._api = mock_api

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

        mock_api = MagicMock()
        mock_api.like = AsyncMock(return_value=ApiResponse(
            ok=True, code=0, raw={"code": 0}
        ))
        client._api = mock_api

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

        mock_api = MagicMock()
        mock_api.comment = AsyncMock(return_value=ApiResponse(
            ok=True, code=0, data={"commentId": "789012"}, raw={"code": 0, "commentId": "789012"}
        ))
        client._api = mock_api

        result = await client.comment_post("123456", 123456789, "test comment")

        assert result.success is True
        assert result.comment_id == "789012"
        assert result.message == "评论成功"