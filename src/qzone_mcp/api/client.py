import asyncio
import logging
from typing import List, Optional, Dict, Any

import aiohttp

from .session import QzoneSession, LoginExpiredError
from .model import Feed, FeedImage, FeedComment, Visitor, PublishResult, LikeResult, CommentResult, ApiResponse
from .parser import QzoneParser
from .constants import (
    HTTP_STATUS_UNAUTHORIZED,
    HTTP_STATUS_FORBIDDEN,
    QZONE_CODE_LOGIN_EXPIRED,
    QZONE_CODE_UNKNOWN,
    QZONE_MSG_PERMISSION_DENIED,
    QZONE_INTERNAL_META_KEY,
    QZONE_INTERNAL_HTTP_STATUS_KEY,
    QZONE_LIST_URL,
    QZONE_DETAIL_URL,
    QZONE_EMOTION_URL,
    QZONE_DOLIKE_URL,
    QZONE_COMMENT_URL,
    QZONE_VISITOR_URL,
    QZONE_BASE_URL,
)

logger = logging.getLogger(__name__)


class QzoneClient:
    def __init__(self, session: QzoneSession):
        self.session = session
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_http_session(self) -> aiohttp.ClientSession:
        if not self._http_session:
            self._http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.session.cfg.qzone.timeout)
            )
        return self._http_session

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
        session = await self._get_http_session()

        kwargs: dict[str, Any] = {
            "params": params or {},
        }
        if data:
            kwargs["data"] = data
        kwargs.setdefault("headers", {})
        kwargs["headers"].update(ctx.headers())
        kwargs["cookies"] = ctx.cookies()

        try:
            async with session.request(method, url, timeout=timeout, **kwargs) as resp:
                text = await resp.text()

            parsed = QzoneParser.parse_response(text)
            meta = parsed.get(QZONE_INTERNAL_META_KEY)
            if not isinstance(meta, dict):
                meta = {}
                parsed[QZONE_INTERNAL_META_KEY] = meta
            meta[QZONE_INTERNAL_HTTP_STATUS_KEY] = resp.status

            if resp.status == HTTP_STATUS_UNAUTHORIZED or parsed.get("code") == QZONE_CODE_LOGIN_EXPIRED:
                if retry >= self.session.cfg.qzone.max_retries:
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
            if retry >= self.session.cfg.qzone.max_retries:
                raise
            await self.session.invalidate()
            await asyncio.sleep(self.session.cfg.qzone.retry_delay * (retry + 1))
            return await self.request(method, url, params=params, data=data, headers=headers, retry=retry + 1)
        except aiohttp.ClientError as e:
            if retry >= self.session.cfg.qzone.max_retries:
                raise
            await asyncio.sleep(self.session.cfg.qzone.retry_delay * (retry + 1))
            return await self.request(method, url, params=params, data=data, headers=headers, retry=retry + 1)

    async def get_feeds(
        self,
        user_id: Optional[str] = None,
        pos: int = 0,
        num: int = 5,
        with_detail: bool = False
    ) -> List[Feed]:
        ctx = await self.session.get_ctx()
        uin = user_id or ctx.uin

        params = {
            "uin": uin,
            "pos": pos,
            "num": num,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        data = await self.request("GET", QZONE_LIST_URL, params=params)
        return QzoneParser.parse_feeds(data, with_detail=with_detail)

    async def get_post_detail(self, tid: str, author_uin: int) -> Feed:
        ctx = await self.session.get_ctx()

        params = {
            "tid": tid,
            "uin": author_uin,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        data = await self.request("GET", QZONE_DETAIL_URL, params=params)
        feeds = QzoneParser.parse_feeds(data, with_detail=True)
        return feeds[0] if feeds else Feed(tid=tid, uin=author_uin, nickname="", content="")

    async def publish_post(self, text: str, image_urls: Optional[List[str]] = None) -> PublishResult:
        ctx = await self.session.get_ctx()

        data: dict[str, Any] = {
            "syn_tweet_verson": "1",
            "paramstr": "1",
            "who": "1",
            "con": text,
            "feedversion": "1",
            "ver": "1",
            "ugc_right": "1",
            "to_sign": "0",
            "hostuin": ctx.uin,
            "code_version": "1",
            "format": "json",
            "qzreferrer": f"{QZONE_BASE_URL}/{ctx.uin}",
        }

        if image_urls:
            data["pic_url"] = "|".join(image_urls)

        resp = await self.request("POST", QZONE_EMOTION_URL, params={"g_tk": ctx.gtk2, "uin": ctx.uin}, data=data)
        logger.debug(f"publish_post response: {resp}")

        api_resp = ApiResponse.from_raw(resp)
        if api_resp.ok:
            tid = api_resp.data.get("tid", "")
            if not tid and api_resp.data.get("feedinfo"):
                import re
                match = re.search(r'fct_\d+_\d+_\d+_(\d+)', api_resp.data["feedinfo"])
                if match:
                    tid = match.group(1)
            logger.info(f"发布说说成功 - tid: {tid}, content: {text[:50]}...")
            return PublishResult(success=True, tid=tid, message="发布成功")
        logger.warning(f"发布说说失败 - content: {text[:50]}..., response: {resp}")
        return PublishResult(success=False, message="发布失败")

    async def like_post(self, tid: str, author_uin: int) -> LikeResult:
        ctx = await self.session.get_ctx()

        data = {
            "qzreferrer": f"{QZONE_BASE_URL}/{ctx.uin}",
            "opuin": ctx.uin,
            "unikey": f"{QZONE_BASE_URL}/{author_uin}/mood/{tid}",
            "curkey": f"{QZONE_BASE_URL}/{author_uin}/mood/{tid}",
            "appid": 311,
            "from": 1,
            "typeid": 0,
            "fid": tid,
            "active": 0,
            "format": "json",
            "fupdate": 1,
        }

        resp = await self.request("POST", QZONE_DOLIKE_URL, params={"g_tk": ctx.gtk2}, data=data)
        api_resp = ApiResponse.from_raw(resp)
        if api_resp.ok:
            return LikeResult(success=True, message="点赞成功")
        return LikeResult(success=False, message="点赞失败")

    async def comment_post(self, tid: str, author_uin: int, content: str) -> CommentResult:
        ctx = await self.session.get_ctx()

        data = {
            "topicId": f"{author_uin}_{tid}__1",
            "uin": ctx.uin,
            "hostUin": author_uin,
            "feedsType": 100,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "plat": "qzone",
            "source": "ic",
            "platformid": 52,
            "format": "fs",
            "ref": "feeds",
            "content": content,
        }

        resp = await self.request("POST", QZONE_COMMENT_URL, params={"g_tk": ctx.gtk2}, data=data)
        api_resp = ApiResponse.from_raw(resp)
        if api_resp.ok or resp.get("result") == 0:
            return CommentResult(success=True, comment_id=str(resp.get("commentId", "")), message="评论成功")
        return CommentResult(success=False, message="评论失败")

    async def reply_comment(self, tid: str, author_uin: int, comment_id: str, content: str) -> CommentResult:
        ctx = await self.session.get_ctx()

        data = {
            "topicId": f"{author_uin}_{tid}__1",
            "uin": ctx.uin,
            "hostUin": author_uin,
            "feedsType": 100,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "plat": "qzone",
            "source": "ic",
            "platformid": 52,
            "format": "fs",
            "ref": "feeds",
            "content": content,
            "commentId": comment_id,
            "commentUin": 0,
            "richval": "",
            "richtype": "",
            "private": "0",
            "paramstr": "2",
            "qzreferrer": f"{QZONE_BASE_URL}/{ctx.uin}/main",
        }

        resp = await self.request("POST", QZONE_COMMENT_URL, params={"g_tk": ctx.gtk2}, data=data)
        api_resp = ApiResponse.from_raw(resp)
        if api_resp.ok or resp.get("result") == 0:
            return CommentResult(success=True, comment_id=str(resp.get("replyId", "")), message="回复成功")
        return CommentResult(success=False, message="回复失败")

    async def get_visitors(self, page: int = 1, num: int = 20) -> str:
        ctx = await self.session.get_ctx()

        params = {
            "uin": ctx.uin,
            "mask": 7,
            "g_tk": ctx.gtk2,
            "page": page,
            "fupdate": 1,
            "clear": 1,
        }

        data = await self.request("GET", QZONE_VISITOR_URL, params=params)
        return QzoneParser.parse_visitors(data)

    async def close(self):
        if self._http_session:
            await self._http_session.close()