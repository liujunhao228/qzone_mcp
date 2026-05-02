from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

from .constants import QZONE_CODE_OK, QZONE_CODE_UNKNOWN, QZONE_INTERNAL_META_KEY


class ApiResponse(BaseModel):
    ok: bool = Field(description="操作是否成功")
    code: int = Field(description="业务状态码")
    message: Optional[str] = Field(default=None, description="错误信息")
    data: Dict[str, Any] = Field(default_factory=dict, description="业务数据")
    raw: Dict[str, Any] = Field(default_factory=dict, description="原始响应")

    @classmethod
    def from_raw(
        cls,
        raw: Dict[str, Any],
        *,
        code_key: str = "code",
        msg_key: str | Tuple[str, ...] = ("message", "msg"),
        data_key: str | None = None,
        success_code: int = QZONE_CODE_OK,
    ) -> "ApiResponse":
        code = raw.get(code_key, QZONE_CODE_UNKNOWN)

        message = None
        if isinstance(msg_key, tuple):
            for k in msg_key:
                if raw.get(k):
                    message = raw.get(k)
                    break
        else:
            message = raw.get(msg_key) or raw.get("data", {}).get(msg_key) or code

        if code == success_code:
            if data_key is None:
                data = raw.get("data", {})
                if not isinstance(data, dict):
                    data = {"result": data}
            else:
                data = raw.get(data_key, {})
            return cls(
                ok=True,
                code=code,
                message=None,
                data=data,
                raw=raw,
            )

        return cls(
            ok=False,
            code=code,
            message=str(message) if message else None,
            data={},
            raw=raw,
        )


class QzoneContext(BaseModel):
    uin: int = Field(description="QQ 号")
    skey: str = Field(description="会话密钥")
    p_skey: str = Field(description="持久化会话密钥")
    cookies_str: str = Field(description="原始 Cookie 字符串")

    @property
    def gtk2(self) -> str:
        hash_val = 5381
        for ch in self.p_skey:
            hash_val += (hash_val << 5) + ord(ch)
        return str(hash_val & 0x7FFFFFFF)

    def cookies(self) -> Dict[str, str]:
        return {
            "uin": f"o{self.uin}",
            "skey": self.skey,
            "p_skey": self.p_skey,
        }

    def headers(self) -> Dict[str, str]:
        return {
            "Cookie": self.cookies_str,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://user.qzone.qq.com/",
        }


class FeedImage(BaseModel):
    url: str = Field(description="图片 URL")
    width: Optional[int] = Field(default=None, description="图片宽度")
    height: Optional[int] = Field(default=None, description="图片高度")


class FeedComment(BaseModel):
    id: str = Field(description="评论 ID")
    uin: int = Field(description="评论者 QQ 号")
    nickname: str = Field(description="评论者昵称")
    content: str = Field(description="评论内容")
    time: str = Field(description="评论时间")


class Feed(BaseModel):
    tid: str = Field(description="说说 ID")
    uin: int = Field(description="发布者 QQ 号")
    nickname: str = Field(description="发布者昵称")
    content: str = Field(description="说说内容")
    images: List[FeedImage] = Field(default=[], description="图片列表")
    likes: int = Field(default=0, description="点赞数")
    comments: int = Field(default=0, description="评论数")
    shares: int = Field(default=0, description="分享数")
    time: str = Field(description="发布时间")
    comment_list: List[FeedComment] = Field(default=[], description="评论列表")
    is_liked: bool = Field(default=False, description="是否已点赞")


class Visitor(BaseModel):
    uin: int = Field(description="访客 QQ 号")
    nickname: str = Field(description="访客昵称")
    avatar: Optional[str] = Field(default=None, description="头像 URL")
    time: str = Field(description="访问时间")


class PublishResult(BaseModel):
    success: bool = Field(description="是否成功")
    tid: Optional[str] = Field(default=None, description="说说 ID")
    message: str = Field(default="", description="结果消息")


class LikeResult(BaseModel):
    success: bool = Field(description="是否成功")
    message: str = Field(default="", description="结果消息")


class CommentResult(BaseModel):
    success: bool = Field(description="是否成功")
    comment_id: Optional[str] = Field(default=None, description="评论 ID")
    message: str = Field(default="", description="结果消息")


class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="是否成功")
    error_code: str = Field(description="错误码")
    error_message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")