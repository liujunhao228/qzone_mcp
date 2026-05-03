import logging
import time
from typing import Any, List, Optional

import base64

from ..model import ApiResponse, Feed, FeedImage, FeedComment
from ..parser import QzoneJsonParser, QzoneHtmlParser
from ..utils import normalize_images
from .client import QzoneHttpClient
from .constants import (
    QZONE_BASE_URL,
    QZONE_EMOTION_URL,
    QZONE_DOLIKE_URL,
    QZONE_LIST_URL,
    QZONE_COMMENT_URL,
    QZONE_VISITOR_URL,
    QZONE_DETAIL_URL,
    QZONE_DELETE_URL,
    QZONE_ZONE_LIST_URL,
    QZONE_UPLOAD_IMAGE_URL,
)

logger = logging.getLogger(__name__)


class QzoneAPI:
    def __init__(self, http_client: QzoneHttpClient):
        self.http_client = http_client

    async def _upload_image(self, image: bytes) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()
        raw = await self.http_client.request(
            "POST",
            QZONE_UPLOAD_IMAGE_URL,
            data={
                "filename": "filename",
                "uploadtype": "1",
                "albumtype": "7",
                "skey": ctx.skey,
                "uin": ctx.uin,
                "p_skey": ctx.p_skey,
                "output_type": "json",
                "base64": "1",
                "picfile": base64.b64encode(image).decode(),
            },
            headers={
                "referer": f"{QZONE_BASE_URL}/{ctx.uin}",
                "origin": QZONE_BASE_URL,
            },
            timeout=60,
        )
        logger.debug(f"图片上传响应: {raw}")
        return ApiResponse.from_raw(raw, code_key="ret", msg_key="msg")

    async def get_feeds(
        self,
        target_id: str,
        *,
        pos: int = 0,
        num: int = 10,
        with_detail: bool = False,
    ) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

        params = {
            "uin": target_id,
            "pos": pos,
            "num": num,
            "format": "json",
            "g_tk": ctx.gtk2,
        }

        data = await self.http_client.request("GET", QZONE_LIST_URL, params=params)
        
        if not isinstance(data, dict):
            return ApiResponse(
                ok=False,
                code=-1,
                message="无效的响应数据",
                data={},
                raw=data,
            )
        
        feeds = QzoneJsonParser.parse_feeds(data, with_detail=with_detail)
        
        return ApiResponse(
            ok=True,
            code=0,
            data={"feeds": [feed.dict() for feed in feeds]},
            raw=data,
        )

    async def get_post_detail(self, tid: str, author_uin: int) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

        params = {
            "tid": tid,
            "uin": author_uin,
            "format": "jsonp",
            "g_tk": ctx.gtk2,
        }

        data = await self.http_client.request("GET", QZONE_DETAIL_URL, params=params)
        
        if not isinstance(data, dict):
            return ApiResponse(
                ok=False,
                code=-1,
                message="无效的响应数据",
                data={},
                raw=data,
            )
        
        feeds = QzoneJsonParser.parse_feeds(data, with_detail=True)
        
        if feeds:
            return ApiResponse(
                ok=True,
                code=0,
                data={"feed": feeds[0].dict()},
                raw=data,
            )
        return ApiResponse(
            ok=True,
            code=0,
            data={"feed": None},
            raw=data,
        )

    async def publish(
        self,
        text: str,
        images: Optional[List[bytes]] = None,
    ) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

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

        if images:
            pic_bos, richvals = [], []
            for img in images:
                resp = await self._upload_image(img)
                if not resp.ok:
                    return ApiResponse(
                        ok=False,
                        code=resp.code,
                        message=resp.message or "图片上传失败",
                        raw=resp.raw,
                    )
                picbo, richval = QzoneJsonParser.parse_upload_result(resp.data)
                pic_bos.append(picbo)
                richvals.append(richval)
            data.update(
                pic_bo=",".join(pic_bos),
                richtype="1",
                richval="\t".join(richvals),
            )

        resp = await self.http_client.request(
            "POST",
            QZONE_EMOTION_URL,
            params={"g_tk": ctx.gtk2, "uin": ctx.uin},
            data=data,
        )
        api_resp = ApiResponse.from_raw(resp)
        
        if api_resp.ok:
            tid = api_resp.data.get("tid", "")
            if not tid and api_resp.data.get("feedinfo"):
                import re
                match = re.search(r'fct_\d+_\d+_\d+_(\d+)', api_resp.data["feedinfo"])
                if match:
                    tid = match.group(1)
            api_resp.data["tid"] = tid
        
        return api_resp

    async def like(self, tid: str, author_uin: int) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

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

        resp = await self.http_client.request("POST", QZONE_DOLIKE_URL, params={"g_tk": ctx.gtk2}, data=data)
        return ApiResponse.from_raw(resp)

    async def comment(self, tid: str, author_uin: int, content: str) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

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

        resp = await self.http_client.request("POST", QZONE_COMMENT_URL, params={"g_tk": ctx.gtk2}, data=data)
        api_resp = ApiResponse.from_raw(resp)
        
        if api_resp.ok or resp.get("result") == 0:
            return ApiResponse(
                ok=True,
                code=0,
                data={"commentId": str(resp.get("commentId", ""))},
                raw=resp,
            )
        return api_resp

    async def reply_comment(
        self,
        tid: str,
        author_uin: int,
        comment_id: str,
        content: str,
    ) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

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

        resp = await self.http_client.request("POST", QZONE_COMMENT_URL, params={"g_tk": ctx.gtk2}, data=data)
        api_resp = ApiResponse.from_raw(resp)
        
        if api_resp.ok or resp.get("result") == 0:
            return ApiResponse(
                ok=True,
                code=0,
                data={"replyId": str(resp.get("replyId", ""))},
                raw=resp,
            )
        return api_resp

    async def delete(self, tid: str) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()
        
        data = {
            "uin": ctx.uin,
            "topicId": f"{ctx.uin}_{tid}__1",
            "feedsType": 0,
            "feedsFlag": 0,
            "feedsKey": tid,
            "feedsAppid": 311,
            "feedsTime": int(time.time()),
            "fupdate": 1,
            "ref": "feeds",
            "qzreferrer": (
                "https://user.qzone.qq.com/"
                f"proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/"
                f"feeds_html_module?g_iframeUser=1&i_uin={ctx.uin}&i_login_uin={ctx.uin}"
                "&mode=4&previewV8=1&style=35&version=8"
                "&needDelOpr=true"
            ),
        }

        resp = await self.http_client.request("POST", QZONE_DELETE_URL, params={"g_tk": ctx.gtk2}, data=data)
        return ApiResponse.from_raw(resp)

    async def get_recent_feeds(self, page: int = 1) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()
        
        params = {
            "uin": ctx.uin,
            "scope": 0,
            "view": 1,
            "filter": "all",
            "flag": 1,
            "applist": "all",
            "pagenum": page,
            "aisortEndTime": 0,
            "aisortOffset": 0,
            "aisortBeginTime": 0,
            "begintime": 0,
            "format": "json",
            "g_tk": ctx.gtk2,
            "useutf8": 1,
            "outputhtmlfeed": 1,
        }

        data = await self.http_client.request("GET", QZONE_ZONE_LIST_URL, params=params)
        
        if not data or not isinstance(data, dict):
            return ApiResponse(
                ok=False,
                code=-1,
                message="无效的响应数据",
                data={},
                raw=data,
            )
        
        return ApiResponse.from_raw(data)

    async def get_visitors(self, page: int = 1, num: int = 20) -> ApiResponse:
        ctx = await self.http_client.session.get_ctx()

        params = {
            "uin": ctx.uin,
            "mask": 7,
            "g_tk": ctx.gtk2,
            "page": page,
            "fupdate": 1,
            "clear": 1,
        }

        data = await self.http_client.request("GET", QZONE_VISITOR_URL, params=params)
        visitors_text = QzoneJsonParser.parse_visitors(data)
        
        return ApiResponse(
            ok=True,
            code=0,
            data={"visitors": visitors_text, "raw": data},
            raw=data,
        )
