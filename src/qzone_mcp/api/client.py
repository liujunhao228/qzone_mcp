import asyncio
from typing import List, Optional, Dict, Any

import aiohttp

from .session import QzoneSession, LoginExpiredError
from .model import Feed, FeedImage, FeedComment, Visitor, PublishResult, LikeResult, CommentResult


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

    async def request(self, method: str, url: str, retry: int = 0, **kwargs) -> Any:
        ctx = await self.session.get_ctx()
        session = await self._get_http_session()

        kwargs.setdefault("headers", {})
        kwargs["headers"].update(ctx.headers())

        try:
            async with session.request(method, url, **kwargs) as resp:
                text = await resp.text()
                if resp.status == 401 or (text and "登录" in text):
                    raise LoginExpiredError("登录失效")
                return await resp.json()
        except LoginExpiredError:
            if retry >= self.session.cfg.qzone.max_retries:
                raise
            await self.session.invalidate()
            await asyncio.sleep(self.session.cfg.qzone.retry_delay * (retry + 1))
            return await self.request(method, url, retry + 1, **kwargs)
        except aiohttp.ClientError as e:
            if retry >= self.session.cfg.qzone.max_retries:
                raise
            await asyncio.sleep(self.session.cfg.qzone.retry_delay * (retry + 1))
            return await self.request(method, url, retry + 1, **kwargs)

    async def get_feeds(
        self,
        user_id: Optional[str] = None,
        pos: int = 0,
        num: int = 5,
        with_detail: bool = False
    ) -> List[Feed]:
        ctx = await self.session.get_ctx()
        uin = user_id or ctx.uin
        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
        
        params = {
            "uin": uin,
            "pos": pos,
            "num": num,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        data = await self.request("GET", url, params=params)
        return self._parse_feeds(data, with_detail=with_detail)

    async def get_post_detail(self, tid: str, author_uin: int) -> Feed:
        ctx = await self.session.get_ctx()
        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6"
        
        params = {
            "tid": tid,
            "uin": author_uin,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        data = await self.request("GET", url, params=params)
        feeds = self._parse_feeds(data, with_detail=True)
        return feeds[0] if feeds else Feed(tid=tid, uin=author_uin, nickname="", content="")

    async def publish_post(self, text: str, image_urls: Optional[List[str]] = None) -> PublishResult:
        ctx = await self.session.get_ctx()
        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_publish_v6"

        data = {
            "content": text,
            "format": "json",
            "g_tk": ctx.gtk2,
            "uin": ctx.uin,
        }

        if image_urls:
            data["pic_url"] = "|".join(image_urls)

        resp = await self.request("POST", url, data=data)
        if resp.get("code") == 0:
            return PublishResult(success=True, tid=resp.get("tid"), message="发布成功")
        return PublishResult(success=False, message=resp.get("message", "发布失败"))

    async def like_post(self, tid: str, author_uin: int) -> LikeResult:
        ctx = await self.session.get_ctx()
        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_like"

        params = {
            "tid": tid,
            "uin": author_uin,
            "cur_uin": ctx.uin,
            "like_num": 1,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        resp = await self.request("GET", url, params=params)
        if resp.get("code") == 0:
            return LikeResult(success=True, message="点赞成功")
        return LikeResult(success=False, message=resp.get("message", "点赞失败"))

    async def comment_post(self, tid: str, author_uin: int, content: str) -> CommentResult:
        ctx = await self.session.get_ctx()
        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_comment"

        data = {
            "tid": tid,
            "uin": author_uin,
            "cur_uin": ctx.uin,
            "content": content,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        resp = await self.request("POST", url, data=data)
        if resp.get("code") == 0:
            return CommentResult(success=True, comment_id=resp.get("commentid"), message="评论成功")
        return CommentResult(success=False, message=resp.get("message", "评论失败"))

    async def reply_comment(self, tid: str, author_uin: int, comment_id: str, content: str) -> CommentResult:
        ctx = await self.session.get_ctx()
        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_reply"

        data = {
            "tid": tid,
            "uin": author_uin,
            "cur_uin": ctx.uin,
            "content": content,
            "replyid": comment_id,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        resp = await self.request("POST", url, data=data)
        if resp.get("code") == 0:
            return CommentResult(success=True, comment_id=resp.get("replyid"), message="回复成功")
        return CommentResult(success=False, message=resp.get("message", "回复失败"))

    async def get_visitors(self, page: int = 1, num: int = 20) -> List[Visitor]:
        ctx = await self.session.get_ctx()
        url = f"https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/main_page_cgi"

        params = {
            "uin": ctx.uin,
            "page": page,
            "num": num,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        data = await self.request("GET", url, params=params)
        return self._parse_visitors(data)

    def _parse_feeds(self, data: Dict[str, Any], with_detail: bool = False) -> List[Feed]:
        feeds = []
        msglist = data.get("msglist", [])
        
        for item in msglist:
            images = []
            if item.get("pic"):
                for pic in item["pic"]:
                    images.append(FeedImage(url=pic.get("url")))
            
            comments = []
            if with_detail and item.get("commentlist"):
                for c in item["commentlist"]:
                    comments.append(FeedComment(
                        id=str(c.get("commentid")),
                        uin=c.get("uin", 0),
                        nickname=c.get("name", ""),
                        content=c.get("content", ""),
                        time=c.get("time", "")
                    ))
            
            feeds.append(Feed(
                tid=str(item.get("tid", "")),
                uin=item.get("uin", 0),
                nickname=item.get("name", ""),
                content=item.get("content", ""),
                images=images,
                likes=item.get("like_num", 0),
                comments=item.get("comment_num", 0),
                shares=item.get("share_num", 0),
                time=item.get("time", ""),
                comment_list=comments,
                is_liked=item.get("is_liked", False)
            ))
        
        return feeds

    def _parse_visitors(self, data: Dict[str, Any]) -> List[Visitor]:
        visitors = []
        visitor_list = data.get("visitor", {}).get("list", [])
        
        for item in visitor_list:
            visitors.append(Visitor(
                uin=item.get("uin", 0),
                nickname=item.get("name", ""),
                avatar=item.get("face", ""),
                time=item.get("time", "")
            ))
        
        return visitors

    async def close(self):
        if self._http_session:
            await self._http_session.close()