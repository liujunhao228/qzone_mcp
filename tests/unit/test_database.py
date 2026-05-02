import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from qzone_mcp.db.models import Feed, Comment, Draft
from qzone_mcp.db.manager import db_manager
from qzone_mcp.db.repository import FeedRepository, CommentRepository, DraftRepository
from qzone_mcp.config import AppConfig


@pytest.fixture(autouse=True)
async def setup_database(tmp_path):
    """测试前初始化数据库，使用临时目录"""
    test_db_path = tmp_path / "test_qzone_mcp.db"
    
    await db_manager.initialize(test_db_path)
    yield
    await db_manager.close()


@pytest.mark.asyncio
async def test_feed_repository_create():
    feed_data = {
        "tid": "test_tid_123",
        "uin": 123456789,
        "content": "测试说说内容",
        "nickname": "测试用户",
        "likes": 10,
        "comments": 5,
        "shares": 2,
        "time": "2024-01-15 10:30",
        "is_liked": False
    }
    
    feed = await FeedRepository.create(feed_data)
    
    assert feed.tid == "test_tid_123"
    assert feed.uin == 123456789
    assert feed.content == "测试说说内容"
    assert feed.nickname == "测试用户"
    assert feed.likes == 10
    assert feed.comments == 5
    assert feed.shares == 2
    assert feed.time == "2024-01-15 10:30"
    assert feed.is_liked is False


@pytest.mark.asyncio
async def test_feed_repository_get_by_tid():
    feed_data = {
        "tid": "test_tid_456",
        "uin": 987654321,
        "content": "查找测试内容",
        "nickname": "查找用户"
    }
    await FeedRepository.create(feed_data)
    
    feed = await FeedRepository.get_by_tid("test_tid_456")
    
    assert feed is not None
    assert feed.tid == "test_tid_456"
    assert feed.uin == 987654321
    assert feed.content == "查找测试内容"


@pytest.mark.asyncio
async def test_feed_repository_get_by_tid_not_found():
    feed = await FeedRepository.get_by_tid("non_existent_tid")
    
    assert feed is None


@pytest.mark.asyncio
async def test_feed_repository_update():
    feed_data = {
        "tid": "test_tid_update",
        "uin": 111111111,
        "content": "原始内容",
        "nickname": "原始昵称"
    }
    await FeedRepository.create(feed_data)
    
    updated = await FeedRepository.update("test_tid_update", {
        "content": "更新后的内容",
        "likes": 20,
        "comments": 8
    })
    
    assert updated is not None
    assert updated.content == "更新后的内容"
    assert updated.likes == 20
    assert updated.comments == 8


@pytest.mark.asyncio
async def test_feed_repository_delete():
    feed_data = {
        "tid": "test_tid_delete",
        "uin": 222222222,
        "content": "要删除的内容"
    }
    await FeedRepository.create(feed_data)
    
    exists_before = await FeedRepository.exists("test_tid_delete")
    assert exists_before is True
    
    success = await FeedRepository.delete("test_tid_delete")
    assert success is True
    
    exists_after = await FeedRepository.exists("test_tid_delete")
    assert exists_after is False


@pytest.mark.asyncio
async def test_feed_repository_count():
    for i in range(5):
        await FeedRepository.create({
            "tid": f"test_tid_count_{i}",
            "uin": 333333333,
            "content": f"内容{i}"
        })
    
    count = await FeedRepository.count()
    
    assert count >= 5


@pytest.mark.asyncio
async def test_feed_repository_exists():
    feed_data = {
        "tid": "test_tid_exists",
        "uin": 444444444,
        "content": "存在测试"
    }
    await FeedRepository.create(feed_data)
    
    assert await FeedRepository.exists("test_tid_exists") is True
    assert await FeedRepository.exists("non_existent") is False


@pytest.mark.asyncio
async def test_comment_repository_create():
    feed_data = {
        "tid": "test_feed_with_comments",
        "uin": 555555555,
        "content": "有评论的说说"
    }
    await FeedRepository.create(feed_data)
    
    comment_data = {
        "comment_id": "c1",
        "tid": "test_feed_with_comments",
        "uin": 666666666,
        "nickname": "评论者",
        "content": "这是一条评论",
        "time": "2024-01-15 11:00"
    }
    
    comment = await CommentRepository.create(comment_data)
    
    assert comment.comment_id == "c1"
    assert comment.tid == "test_feed_with_comments"
    assert comment.uin == 666666666
    assert comment.content == "这是一条评论"


@pytest.mark.asyncio
async def test_comment_repository_create_batch():
    feed_data = {
        "tid": "test_feed_batch",
        "uin": 777777777,
        "content": "批量评论测试"
    }
    await FeedRepository.create(feed_data)
    
    comments_data = [
        {
            "comment_id": "c1",
            "tid": "test_feed_batch",
            "uin": 888888888,
            "nickname": "评论者1",
            "content": "评论1"
        },
        {
            "comment_id": "c2",
            "tid": "test_feed_batch",
            "uin": 999999999,
            "nickname": "评论者2",
            "content": "评论2"
        }
    ]
    
    comments = await CommentRepository.create_batch(comments_data)
    
    assert len(comments) == 2
    assert comments[0].comment_id == "c1"
    assert comments[1].comment_id == "c2"


@pytest.mark.asyncio
async def test_comment_repository_get_by_tid():
    feed_data = {
        "tid": "test_feed_get_comments",
        "uin": 1122334455,
        "content": "获取评论测试"
    }
    await FeedRepository.create(feed_data)
    
    await CommentRepository.create({
        "comment_id": "c_get_1",
        "tid": "test_feed_get_comments",
        "uin": 111111111,
        "content": "评论1"
    })
    await CommentRepository.create({
        "comment_id": "c_get_2",
        "tid": "test_feed_get_comments",
        "uin": 222222222,
        "content": "评论2"
    })
    
    comments = await CommentRepository.get_by_tid("test_feed_get_comments")
    
    assert len(comments) == 2
    assert comments[0].comment_id == "c_get_1"
    assert comments[1].comment_id == "c_get_2"


@pytest.mark.asyncio
async def test_comment_repository_delete_by_tid():
    feed_data = {
        "tid": "test_feed_delete_comments",
        "uin": 5566778899,
        "content": "删除评论测试"
    }
    await FeedRepository.create(feed_data)
    
    await CommentRepository.create({
        "comment_id": "c_del_1",
        "tid": "test_feed_delete_comments",
        "uin": 111111111,
        "content": "评论"
    })
    
    count_before = await CommentRepository.count_by_tid("test_feed_delete_comments")
    assert count_before == 1
    
    deleted = await CommentRepository.delete_by_tid("test_feed_delete_comments")
    assert deleted == 1
    
    count_after = await CommentRepository.count_by_tid("test_feed_delete_comments")
    assert count_after == 0


@pytest.mark.asyncio
async def test_feed_deletion_cascades_comments():
    feed_data = {
        "tid": "test_cascade_feed",
        "uin": 123123123,
        "content": "级联删除测试"
    }
    await FeedRepository.create(feed_data)
    
    await CommentRepository.create({
        "comment_id": "c_cascade_1",
        "tid": "test_cascade_feed",
        "uin": 456456456,
        "content": "级联测试评论"
    })
    
    comments_before = await CommentRepository.get_by_tid("test_cascade_feed")
    assert len(comments_before) == 1
    
    await FeedRepository.delete("test_cascade_feed")
    
    comments_after = await CommentRepository.get_by_tid("test_cascade_feed")
    assert len(comments_after) == 0


@pytest.mark.asyncio
async def test_feed_to_dict():
    feed_data = {
        "tid": "test_dict_tid",
        "uin": 789789789,
        "content": "字典转换测试",
        "nickname": "测试用户",
        "likes": 5,
        "comments": 2,
        "shares": 1,
        "time": "2024-01-15 12:00",
        "is_liked": True
    }
    feed = await FeedRepository.create(feed_data)
    
    feed_dict = feed.to_dict()
    
    assert feed_dict["tid"] == "test_dict_tid"
    assert feed_dict["uin"] == 789789789
    assert feed_dict["content"] == "字典转换测试"
    assert feed_dict["nickname"] == "测试用户"
    assert feed_dict["likes"] == 5
    assert feed_dict["comments"] == 2
    assert feed_dict["shares"] == 1
    assert feed_dict["time"] == "2024-01-15 12:00"
    assert feed_dict["is_liked"] is True
    assert "created_at" in feed_dict
    assert "updated_at" in feed_dict
