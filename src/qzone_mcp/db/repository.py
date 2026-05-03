import json
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Feed, Comment, Draft, Visitor, UserProfile, LikeRecord
from .manager import db_manager


class FeedRepository:
    """说说数据访问层 - 提供说说数据的CRUD操作"""
    
    @staticmethod
    async def create(feed_data: Dict[str, Any]) -> Feed:
        """创建说说记录"""
        session = await db_manager.get_session()
        async with session:
            feed = Feed(**feed_data)
            session.add(feed)
            await session.commit()
            await session.refresh(feed)
            return feed
    
    @staticmethod
    async def get_by_tid(tid: str) -> Optional[Feed]:
        """根据说说ID获取说说"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(select(Feed).filter_by(tid=tid))
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_uin(uin: int, limit: int = 20, offset: int = 0) -> List[Feed]:
        """根据发布者QQ号获取说说列表"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Feed)
                .filter_by(uin=uin)
                .order_by(desc(Feed.time))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_all(limit: int = 20, offset: int = 0) -> List[Feed]:
        """获取所有说说列表"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Feed)
                .order_by(desc(Feed.created_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def update(tid: str, update_data: Dict[str, Any]) -> Optional[Feed]:
        """更新说说记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                update(Feed)
                .filter_by(tid=tid)
                .values(update_data)
                .returning(Feed)
            )
            await session.commit()
            return result.scalar_one_or_none()
    
    @staticmethod
    async def delete(tid: str) -> bool:
        """删除说说记录（级联删除关联评论）"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(Feed)
                .filter_by(tid=tid)
            )
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def count() -> int:
        """获取说说总数"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(select(func.count()).select_from(Feed))
            return result.scalar_one()
    
    @staticmethod
    async def exists(tid: str) -> bool:
        """检查说说是否存在"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Feed.id)
                .filter_by(tid=tid)
                .limit(1)
            )
            return result.scalar_one_or_none() is not None


class CommentRepository:
    """评论数据访问层 - 提供评论数据的CRUD操作"""
    
    @staticmethod
    async def create(comment_data: Dict[str, Any]) -> Comment:
        """创建评论记录"""
        session = await db_manager.get_session()
        async with session:
            comment = Comment(**comment_data)
            session.add(comment)
            await session.commit()
            await session.refresh(comment)
            return comment
    
    @staticmethod
    async def create_batch(comments_data: List[Dict[str, Any]]) -> List[Comment]:
        """批量创建评论记录"""
        session = await db_manager.get_session()
        async with session:
            comments = [Comment(**data) for data in comments_data]
            session.add_all(comments)
            await session.commit()
            return comments
    
    @staticmethod
    async def get_by_tid(tid: str) -> List[Comment]:
        """根据说说ID获取评论列表"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Comment)
                .filter_by(tid=tid)
                .order_by(Comment.time)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_by_comment_id(comment_id: str) -> Optional[Comment]:
        """根据评论ID获取评论"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Comment)
                .filter_by(comment_id=comment_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_by_tid(tid: str) -> int:
        """删除指定说说的所有评论"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(Comment)
                .filter_by(tid=tid)
            )
            await session.commit()
            return result.rowcount
    
    @staticmethod
    async def count_by_tid(tid: str) -> int:
        """获取指定说说的评论数"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(func.count()).select_from(Comment).filter_by(tid=tid)
            )
            return result.scalar_one()


class DraftRepository:
    """草稿数据访问层 - 提供草稿数据的CRUD操作"""
    
    @staticmethod
    async def create(draft_data: Dict[str, Any]) -> Draft:
        """创建草稿记录"""
        session = await db_manager.get_session()
        async with session:
            draft = Draft(**draft_data)
            session.add(draft)
            await session.commit()
            await session.refresh(draft)
            return draft
    
    @staticmethod
    async def get_by_id(draft_id: str) -> Optional[Draft]:
        """根据草稿ID获取草稿"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Draft)
                .filter_by(id=draft_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Draft]:
        """获取草稿列表"""
        session = await db_manager.get_session()
        async with session:
            query = select(Draft).order_by(desc(Draft.updated_at))
            
            if status:
                query = query.filter_by(status=status)
            
            result = await session.execute(
                query.limit(limit).offset(offset)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def update(draft_id: str, update_data: Dict[str, Any]) -> Optional[Draft]:
        """更新草稿记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                update(Draft)
                .filter_by(id=draft_id)
                .values(update_data)
                .returning(Draft)
            )
            await session.commit()
            return result.scalar_one_or_none()
    
    @staticmethod
    async def delete(draft_id: str) -> bool:
        """硬删除草稿记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(Draft)
                .filter_by(id=draft_id)
            )
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def soft_delete(draft_id: str) -> bool:
        """软删除草稿（标记为已删除）"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                update(Draft)
                .filter_by(id=draft_id)
                .values(status="deleted")
            )
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def count(status: Optional[str] = None) -> int:
        """获取草稿总数"""
        session = await db_manager.get_session()
        async with session:
            query = select(func.count()).select_from(Draft)
            
            if status:
                query = query.filter_by(status=status)
            
            result = await session.execute(query)
            return result.scalar_one()
    
    @staticmethod
    async def exists(draft_id: str) -> bool:
        """检查草稿是否存在"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Draft.id)
                .filter_by(id=draft_id)
                .limit(1)
            )
            return result.scalar_one_or_none() is not None


class VisitorRepository:
    """访客数据访问层 - 提供访客数据的CRUD操作"""
    
    @staticmethod
    async def create(visitor_data: Dict[str, Any]) -> Visitor:
        """创建访客记录"""
        session = await db_manager.get_session()
        async with session:
            visitor = Visitor(**visitor_data)
            session.add(visitor)
            await session.commit()
            await session.refresh(visitor)
            return visitor
    
    @staticmethod
    async def create_batch(visitors_data: List[Dict[str, Any]]) -> List[Visitor]:
        """批量创建访客记录"""
        session = await db_manager.get_session()
        async with session:
            visitors = [Visitor(**data) for data in visitors_data]
            session.add_all(visitors)
            await session.commit()
            return visitors
    
    @staticmethod
    async def get_by_uin(uin: int) -> Optional[Visitor]:
        """根据访客QQ号获取访客记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(select(Visitor).filter_by(uin=uin))
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(limit: int = 50, offset: int = 0) -> List[Visitor]:
        """获取所有访客记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Visitor)
                .order_by(desc(Visitor.time))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def update(uin: int, update_data: Dict[str, Any]) -> Optional[Visitor]:
        """更新访客记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                update(Visitor)
                .filter_by(uin=uin)
                .values(update_data)
                .returning(Visitor)
            )
            await session.commit()
            return result.scalar_one_or_none()
    
    @staticmethod
    async def delete(uin: int) -> bool:
        """删除访客记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(Visitor)
                .filter_by(uin=uin)
            )
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def count() -> int:
        """获取访客总数"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(select(func.count()).select_from(Visitor))
            return result.scalar_one()
    
    @staticmethod
    async def exists(uin: int) -> bool:
        """检查访客是否存在"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(Visitor.id)
                .filter_by(uin=uin)
                .limit(1)
            )
            return result.scalar_one_or_none() is not None


class UserProfileRepository:
    """用户信息数据访问层 - 提供用户信息数据的CRUD操作"""
    
    @staticmethod
    async def create(profile_data: Dict[str, Any]) -> UserProfile:
        """创建用户信息记录"""
        session = await db_manager.get_session()
        async with session:
            profile = UserProfile(**profile_data)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            return profile
    
    @staticmethod
    async def get_by_uin(uin: int) -> Optional[UserProfile]:
        """根据QQ号获取用户信息"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(select(UserProfile).filter_by(uin=uin))
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(limit: int = 20, offset: int = 0) -> List[UserProfile]:
        """获取所有用户信息"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(UserProfile)
                .order_by(desc(UserProfile.updated_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def update(uin: int, update_data: Dict[str, Any]) -> Optional[UserProfile]:
        """更新用户信息"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                update(UserProfile)
                .filter_by(uin=uin)
                .values(update_data)
                .returning(UserProfile)
            )
            await session.commit()
            return result.scalar_one_or_none()
    
    @staticmethod
    async def upsert(profile_data: Dict[str, Any]) -> UserProfile:
        """更新或插入用户信息"""
        session = await db_manager.get_session()
        async with session:
            uin = profile_data.get("uin")
            existing = await session.execute(select(UserProfile).filter_by(uin=uin))
            existing = existing.scalar_one_or_none()
            
            if existing:
                for key, value in profile_data.items():
                    setattr(existing, key, value)
            else:
                existing = UserProfile(**profile_data)
                session.add(existing)
            
            await session.commit()
            await session.refresh(existing)
            return existing
    
    @staticmethod
    async def delete(uin: int) -> bool:
        """删除用户信息"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(UserProfile)
                .filter_by(uin=uin)
            )
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def count() -> int:
        """获取用户信息总数"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(select(func.count()).select_from(UserProfile))
            return result.scalar_one()
    
    @staticmethod
    async def exists(uin: int) -> bool:
        """检查用户信息是否存在"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(UserProfile.id)
                .filter_by(uin=uin)
                .limit(1)
            )
            return result.scalar_one_or_none() is not None


class LikeRecordRepository:
    """点赞记录数据访问层 - 提供点赞记录数据的CRUD操作"""
    
    @staticmethod
    async def create(like_data: Dict[str, Any]) -> LikeRecord:
        """创建点赞记录"""
        session = await db_manager.get_session()
        async with session:
            like = LikeRecord(**like_data)
            session.add(like)
            await session.commit()
            await session.refresh(like)
            return like
    
    @staticmethod
    async def create_batch(likes_data: List[Dict[str, Any]]) -> List[LikeRecord]:
        """批量创建点赞记录"""
        session = await db_manager.get_session()
        async with session:
            likes = [LikeRecord(**data) for data in likes_data]
            session.add_all(likes)
            await session.commit()
            return likes
    
    @staticmethod
    async def get_by_tid(tid: str) -> List[LikeRecord]:
        """根据说说ID获取点赞记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(LikeRecord)
                .filter_by(tid=tid)
                .order_by(LikeRecord.created_at)
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_by_tid_and_uin(tid: str, uin: int) -> Optional[LikeRecord]:
        """根据说说ID和点赞者QQ号获取点赞记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(LikeRecord)
                .filter_by(tid=tid, uin=uin)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_by_tid(tid: str) -> int:
        """删除指定说说的所有点赞记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(LikeRecord)
                .filter_by(tid=tid)
            )
            await session.commit()
            return result.rowcount
    
    @staticmethod
    async def delete_by_tid_and_uin(tid: str, uin: int) -> bool:
        """删除指定说说的指定点赞记录"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                delete(LikeRecord)
                .filter_by(tid=tid, uin=uin)
            )
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def count_by_tid(tid: str) -> int:
        """获取指定说说的点赞数"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(func.count()).select_from(LikeRecord).filter_by(tid=tid)
            )
            return result.scalar_one()
    
    @staticmethod
    async def exists(tid: str, uin: int) -> bool:
        """检查点赞记录是否存在"""
        session = await db_manager.get_session()
        async with session:
            result = await session.execute(
                select(LikeRecord.id)
                .filter_by(tid=tid, uin=uin)
                .limit(1)
            )
            return result.scalar_one_or_none() is not None
