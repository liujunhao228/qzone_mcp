from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, Boolean, DateTime, Index, ForeignKey
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy 基础模型类"""
    pass


class Feed(Base):
    """说说模型 - 存储QQ空间说说数据"""
    __tablename__ = "feeds"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    tid = Column(String(64), nullable=False, unique=True, comment="说说ID（QQ空间唯一标识）")
    uin = Column(BigInteger, nullable=False, comment="发布者QQ号")
    nickname = Column(String(128), comment="发布者昵称")
    content = Column(Text, comment="说说内容")
    images = Column(Text, comment="图片URL列表（JSON格式）")
    likes = Column(Integer, default=0, comment="点赞数")
    comments = Column(Integer, default=0, comment="评论数")
    shares = Column(Integer, default=0, comment="分享数")
    time = Column(String(32), comment="发布时间")
    is_liked = Column(Boolean, default=False, comment="是否已点赞")
    created_at = Column(DateTime, default=datetime.now, comment="记录创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="记录更新时间")
    
    # 关联关系
    comment_list = relationship("Comment", back_populates="feed", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_feeds_uin", "uin"),
        Index("idx_feeds_time", "time"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        return {
            "id": self.id,
            "tid": self.tid,
            "uin": self.uin,
            "nickname": self.nickname,
            "content": self.content,
            "images": self.images,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "time": self.time,
            "is_liked": self.is_liked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Comment(Base):
    """评论模型 - 存储说说评论数据"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    comment_id = Column(String(64), nullable=False, comment="评论ID")
    tid = Column(String(64), ForeignKey("feeds.tid", ondelete="CASCADE"), nullable=False, comment="所属说说ID")
    uin = Column(BigInteger, nullable=False, comment="评论者QQ号")
    nickname = Column(String(128), comment="评论者昵称")
    content = Column(Text, comment="评论内容")
    time = Column(String(32), comment="评论时间")
    parent_id = Column(String(64), comment="父评论ID（用于回复）")
    created_at = Column(DateTime, default=datetime.now, comment="记录创建时间")
    
    # 关联关系
    feed = relationship("Feed", back_populates="comment_list")
    
    __table_args__ = (
        Index("idx_comments_tid", "tid"),
        Index("idx_comments_parent_id", "parent_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        return {
            "id": self.id,
            "comment_id": self.comment_id,
            "tid": self.tid,
            "uin": self.uin,
            "nickname": self.nickname,
            "content": self.content,
            "time": self.time,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Draft(Base):
    """草稿模型 - 存储未发布的说说草稿"""
    __tablename__ = "drafts"
    
    id = Column(String(36), primary_key=True, comment="草稿UUID")
    title = Column(String(256), comment="草稿标题")
    content = Column(Text, nullable=False, comment="草稿内容")
    images = Column(Text, comment="图片URL列表（JSON格式）")
    status = Column(String(16), default="draft", comment="状态：draft/published/deleted")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="最后修改时间")
    
    __table_args__ = (
        Index("idx_drafts_status", "status"),
        Index("idx_drafts_updated_at", "updated_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "images": self.images,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
