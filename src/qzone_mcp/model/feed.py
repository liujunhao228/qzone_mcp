from typing import List, Optional
from pydantic import BaseModel, Field


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
    parent_id: Optional[str] = Field(default=None, description="父评论 ID，用于楼中楼")


class Feed(BaseModel):
    tid: str = Field(description="说说 ID")
    uin: int = Field(description="发布者 QQ 号")
    nickname: str = Field(description="发布者昵称")
    content: str = Field(description="说说内容")
    images: List[FeedImage] = Field(default=[], description="图片列表")
    likes: int = Field(default=0, description="点赞数")
    comments: int = Field(default=0, description="评论数")
    shares: int = Field(default=0, description="分享数")
    views: int = Field(default=0, description="浏览数")
    time: Optional[str] = Field(default=None, description="发布时间")
    comment_list: List[FeedComment] = Field(default=[], description="评论列表")
    is_liked: bool = Field(default=False, description="是否已点赞")
    videos: List[str] = Field(default=[], description="视频 URL 列表")
    rt_con: str = Field(default="", description="转发内容")
    source_name: str = Field(default="", description="发布来源")


class Visitor(BaseModel):
    uin: int = Field(description="访客 QQ 号")
    nickname: str = Field(description="访客昵称")
    avatar: Optional[str] = Field(default=None, description="头像 URL")
    time: str = Field(description="访问时间")
