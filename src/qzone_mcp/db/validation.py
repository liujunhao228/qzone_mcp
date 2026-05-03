from typing import Dict, List, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..logging import get_logger
from .manager import db_manager
from .models import Feed, Comment, Draft, Visitor, UserProfile, LikeRecord
from .repository import (
    FeedRepository,
    CommentRepository,
    DraftRepository,
    VisitorRepository,
    UserProfileRepository,
    LikeRecordRepository
)

logger = get_logger(__name__)


class DataValidator:
    """数据验证器 - 负责验证数据库数据的完整性和一致性"""
    
    @staticmethod
    async def validate_integrity() -> Dict[str, Any]:
        """验证数据库数据完整性"""
        results = {
            "status": "success",
            "tables": {},
            "issues": [],
            "summary": {}
        }
        
        try:
            # 验证说说表
            feed_result = await DataValidator._validate_feed_table()
            results["tables"]["feeds"] = feed_result
            if feed_result.get("issues"):
                results["issues"].extend(feed_result["issues"])
            
            # 验证评论表
            comment_result = await DataValidator._validate_comment_table()
            results["tables"]["comments"] = comment_result
            if comment_result.get("issues"):
                results["issues"].extend(comment_result["issues"])
            
            # 验证草稿表
            draft_result = await DataValidator._validate_draft_table()
            results["tables"]["drafts"] = draft_result
            if draft_result.get("issues"):
                results["issues"].extend(draft_result["issues"])
            
            # 验证访客表
            visitor_result = await DataValidator._validate_visitor_table()
            results["tables"]["visitors"] = visitor_result
            if visitor_result.get("issues"):
                results["issues"].extend(visitor_result["issues"])
            
            # 验证用户信息表
            profile_result = await DataValidator._validate_profile_table()
            results["tables"]["user_profiles"] = profile_result
            if profile_result.get("issues"):
                results["issues"].extend(profile_result["issues"])
            
            # 验证点赞记录表
            like_result = await DataValidator._validate_like_table()
            results["tables"]["like_records"] = like_result
            if like_result.get("issues"):
                results["issues"].extend(like_result["issues"])
            
            # 验证外键一致性
            fk_result = await DataValidator._validate_foreign_keys()
            results["tables"]["foreign_keys"] = fk_result
            if fk_result.get("issues"):
                results["issues"].extend(fk_result["issues"])
            
            # 生成摘要
            results["summary"] = {
                "total_tables": 6,
                "valid_tables": sum(1 for t in results["tables"].values() if t["valid"]),
                "total_issues": len(results["issues"]),
                "data_count": {
                    "feeds": feed_result["count"],
                    "comments": comment_result["count"],
                    "drafts": draft_result["count"],
                    "visitors": visitor_result["count"],
                    "user_profiles": profile_result["count"],
                    "like_records": like_result["count"]
                }
            }
            
            if results["issues"]:
                results["status"] = "warning"
            
        except Exception as e:
            logger.error(f"数据完整性验证失败: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    @staticmethod
    async def _validate_feed_table() -> Dict[str, Any]:
        """验证说说表"""
        result = {"valid": True, "count": 0, "issues": []}
        
        try:
            count = await FeedRepository.count()
            result["count"] = count
            
            # 检查是否有无效数据
            session = await db_manager.get_session()
            async with session:
                # 检查空内容
                empty_content = await session.execute(
                    select(func.count()).select_from(Feed).filter(Feed.content.is_(None) | (Feed.content == ""))
                )
                empty_count = empty_content.scalar_one()
                if empty_count > 0:
                    result["valid"] = False
                    result["issues"].append(f"发现 {empty_count} 条内容为空的说说")
                
                # 检查空tid
                empty_tid = await session.execute(
                    select(func.count()).select_from(Feed).filter(Feed.tid.is_(None) | (Feed.tid == ""))
                )
                if empty_tid.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现tid为空的说说")
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def _validate_comment_table() -> Dict[str, Any]:
        """验证评论表"""
        result = {"valid": True, "count": 0, "issues": []}
        
        try:
            count = await CommentRepository.count_by_tid("")
            # 需要单独查询总数
            session = await db_manager.get_session()
            async with session:
                total = await session.execute(select(func.count()).select_from(Comment))
                result["count"] = total.scalar_one()
                
                # 检查空内容
                empty_content = await session.execute(
                    select(func.count()).select_from(Comment).filter(Comment.content.is_(None) | (Comment.content == ""))
                )
                if empty_content.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现内容为空的评论")
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def _validate_draft_table() -> Dict[str, Any]:
        """验证草稿表"""
        result = {"valid": True, "count": 0, "issues": []}
        
        try:
            count = await DraftRepository.count()
            result["count"] = count
            
            # 检查空内容
            session = await db_manager.get_session()
            async with session:
                empty_content = await session.execute(
                    select(func.count()).select_from(Draft).filter(Draft.content.is_(None) | (Draft.content == ""))
                )
                if empty_content.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现内容为空的草稿")
                
                # 检查无效状态
                invalid_status = await session.execute(
                    select(func.count()).select_from(Draft).filter(
                        Draft.status.not_in(["draft", "published", "deleted"])
                    )
                )
                if invalid_status.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现状态无效的草稿")
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def _validate_visitor_table() -> Dict[str, Any]:
        """验证访客表"""
        result = {"valid": True, "count": 0, "issues": []}
        
        try:
            count = await VisitorRepository.count()
            result["count"] = count
            
            # 检查空昵称
            session = await db_manager.get_session()
            async with session:
                empty_nickname = await session.execute(
                    select(func.count()).select_from(Visitor).filter(Visitor.nickname.is_(None) | (Visitor.nickname == ""))
                )
                if empty_nickname.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现昵称为空的访客记录")
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def _validate_profile_table() -> Dict[str, Any]:
        """验证用户信息表"""
        result = {"valid": True, "count": 0, "issues": []}
        
        try:
            count = await UserProfileRepository.count()
            result["count"] = count
            
            # 检查空昵称
            session = await db_manager.get_session()
            async with session:
                empty_nickname = await session.execute(
                    select(func.count()).select_from(UserProfile).filter(
                        UserProfile.nickname.is_(None) | (UserProfile.nickname == "")
                    )
                )
                if empty_nickname.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现昵称为空的用户信息")
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def _validate_like_table() -> Dict[str, Any]:
        """验证点赞记录表"""
        result = {"valid": True, "count": 0, "issues": []}
        
        try:
            session = await db_manager.get_session()
            async with session:
                total = await session.execute(select(func.count()).select_from(LikeRecord))
                result["count"] = total.scalar_one()
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def _validate_foreign_keys() -> Dict[str, Any]:
        """验证外键一致性"""
        result = {"valid": True, "issues": []}
        
        try:
            session = await db_manager.get_session()
            async with session:
                # 检查评论引用的说说是否存在
                orphan_comments = await session.execute(
                    select(func.count()).select_from(Comment)
                    .outerjoin(Feed, Comment.tid == Feed.tid)
                    .filter(Feed.tid.is_(None))
                )
                orphan_count = orphan_comments.scalar_one()
                if orphan_count > 0:
                    result["valid"] = False
                    result["issues"].append(f"发现 {orphan_count} 条引用不存在说说的评论")
                
                # 检查点赞记录引用的说说是否存在
                orphan_likes = await session.execute(
                    select(func.count()).select_from(LikeRecord)
                    .outerjoin(Feed, LikeRecord.tid == Feed.tid)
                    .filter(Feed.tid.is_(None))
                )
                if orphan_likes.scalar_one() > 0:
                    result["valid"] = False
                    result["issues"].append("发现引用不存在说说的点赞记录")
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"外键验证失败: {str(e)}")
        
        return result
    
    @staticmethod
    async def repair_orphan_records() -> Dict[str, Any]:
        """修复孤儿记录（引用了不存在父记录的记录）"""
        results = {
            "status": "success",
            "deleted": {
                "comments": 0,
                "like_records": 0
            },
            "errors": []
        }
        
        try:
            session = await db_manager.get_session()
            async with session:
                # 删除引用不存在说说的评论
                orphan_comments = await session.execute(
                    Comment.__table__.delete()
                    .where(Comment.tid.not_in(select(Feed.tid)))
                )
                await session.commit()
                results["deleted"]["comments"] = orphan_comments.rowcount
                
                # 删除引用不存在说说的点赞记录
                orphan_likes = await session.execute(
                    LikeRecord.__table__.delete()
                    .where(LikeRecord.tid.not_in(select(Feed.tid)))
                )
                await session.commit()
                results["deleted"]["like_records"] = orphan_likes.rowcount
                
                logger.info(f"已修复孤儿记录: 评论 {results['deleted']['comments']} 条, 点赞记录 {results['deleted']['like_records']} 条")
        
        except Exception as e:
            logger.error(f"修复孤儿记录失败: {e}")
            results["status"] = "error"
            results["errors"].append(str(e))
        
        return results
    
    @staticmethod
    async def get_database_stats() -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {}
        
        try:
            stats["feeds"] = await FeedRepository.count()
            stats["comments"] = await CommentRepository.count_by_tid("")
            stats["drafts"] = await DraftRepository.count()
            stats["visitors"] = await VisitorRepository.count()
            stats["user_profiles"] = await UserProfileRepository.count()
            
            # 点赞记录需要单独统计
            session = await db_manager.get_session()
            async with session:
                result = await session.execute(select(func.count()).select_from(LikeRecord))
                stats["like_records"] = result.scalar_one()
            
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
        
        return stats


# 创建全局数据验证器实例
data_validator = DataValidator()