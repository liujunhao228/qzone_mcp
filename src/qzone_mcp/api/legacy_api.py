"""
兼容层 - 提供与旧 API 兼容的接口
用于平滑迁移，保留旧版本的 API 接口签名
"""
import logging
from typing import List, Optional

from ..config import config
from ..model import Feed, FeedImage, FeedComment, Visitor, ApiResponse
from ..parser import QzoneJsonParser
from .client import QzoneHttpClient
from .qzone_api import QzoneAPI
from .constants import (
    QZONE_LIST_URL,
    QZONE_DETAIL_URL,
    QZONE_EMOTION_URL,
    QZONE_DOLIKE_URL,
    QZONE_COMMENT_URL,
    QZONE_VISITOR_URL,
)

logger = logging.getLogger(__name__)


class PublishResult:
    def __init__(self, success: bool, tid: Optional[str] = None, message: str = ""):
        self.success = success
        self.tid = tid
        self.message = message
    
    def model_dump(self):
        return {
            "success": self.success,
            "tid": self.tid,
            "message": self.message
        }


class LikeResult:
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message
    
    def model_dump(self):
        return {
            "success": self.success,
            "message": self.message
        }


class CommentResult:
    def __init__(self, success: bool, comment_id: Optional[str] = None, message: str = ""):
        self.success = success
        self.comment_id = comment_id
        self.message = message
    
    def model_dump(self):
        return {
            "success": self.success,
            "comment_id": self.comment_id,
            "message": self.message
        }


class QzoneClient:
    """
    兼容旧 API 的客户端类
    提供与原 QzoneClient 相同的接口签名
    """
    
    def __init__(self, session):
        self.session = session
        self._http_client = QzoneHttpClient(session, config)
        self._api = QzoneAPI(self._http_client)
        self._http_session = None
    
    async def _get_http_session(self):
        return await self._http_client._get_http_session()
    
    async def request(self, method, url, *, params=None, data=None, headers=None, timeout=None, retry=0):
        return await self._http_client.request(
            method, url, params=params, data=data, headers=headers, timeout=timeout, retry=retry
        )
    
    async def get_feeds(
        self,
        user_id: Optional[str] = None,
        pos: int = 0,
        num: int = 5,
        with_detail: bool = False
    ) -> List[Feed]:
        resp = await self._api.get_feeds(user_id or "", pos=pos, num=num, with_detail=with_detail)
        if resp.ok:
            feeds_data = resp.data.get("feeds", [])
            return [Feed(**feed) for feed in feeds_data]
        return []
    
    async def get_post_detail(self, tid: str, author_uin: int) -> Feed:
        resp = await self._api.get_post_detail(tid, author_uin)
        if resp.ok and resp.data.get("feed"):
            return Feed(**resp.data["feed"])
        return Feed(tid=tid, uin=author_uin, nickname="", content="")
    
    async def publish_post(self, text: str, image_urls: Optional[List[str]] = None) -> PublishResult:
        import asyncio
        from ..utils import normalize_images
        
        images = None
        if image_urls:
            images = await normalize_images(image_urls)
        
        resp = await self._api.publish(text, images)
        
        if resp.ok:
            tid = resp.data.get("tid", "")
            logger.info(f"发布说说成功 - tid: {tid}, content: {text[:50]}...")
            return PublishResult(success=True, tid=tid, message="发布成功")
        logger.warning(f"发布说说失败 - content: {text[:50]}..., response: {resp.raw}")
        return PublishResult(success=False, message="发布失败")
    
    async def like_post(self, tid: str, author_uin: int) -> LikeResult:
        resp = await self._api.like(tid, author_uin)
        if resp.ok:
            return LikeResult(success=True, message="点赞成功")
        return LikeResult(success=False, message="点赞失败")
    
    async def comment_post(self, tid: str, author_uin: int, content: str) -> CommentResult:
        resp = await self._api.comment(tid, author_uin, content)
        if resp.ok:
            comment_id = resp.data.get("commentId", "")
            return CommentResult(success=True, comment_id=comment_id, message="评论成功")
        return CommentResult(success=False, message="评论失败")
    
    async def reply_comment(self, tid: str, author_uin: int, comment_id: str, content: str) -> CommentResult:
        resp = await self._api.reply_comment(tid, author_uin, comment_id, content)
        if resp.ok:
            reply_id = resp.data.get("replyId", "")
            return CommentResult(success=True, comment_id=reply_id, message="回复成功")
        return CommentResult(success=False, message="回复失败")
    
    async def get_friend_feeds(self, pos: int = 0, num: int = 5) -> List[Feed]:
        page = pos // num + 1
        resp = await self._api.get_recent_feeds(page)
        if resp.ok and resp.data:
            from ..parser import QzoneHtmlParser
            feeds = QzoneHtmlParser.parse_recent_feeds(resp.data)
            return feeds[pos : pos + num]
        return []
    
    async def get_visitors(self, page: int = 1, num: int = 20) -> str:
        resp = await self._api.get_visitors(page, num)
        if resp.ok:
            return resp.data.get("visitors", "暂无访客记录")
        return "暂无访客记录"
    
    async def close(self):
        await self._http_client.close()
