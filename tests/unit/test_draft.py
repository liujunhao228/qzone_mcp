import pytest
import json
import uuid
from pathlib import Path

from qzone_mcp.db.models import Draft
from qzone_mcp.db.manager import db_manager
from qzone_mcp.db.repository import DraftRepository
from qzone_mcp.draft.service import DraftService
from qzone_mcp.config import AppConfig


@pytest.fixture(autouse=True)
async def setup_database(tmp_path):
    """测试前初始化数据库，使用临时目录"""
    await db_manager.initialize(tmp_path / "test_draft.db")
    yield
    await db_manager.close()


@pytest.fixture
def mock_qzone_client():
    """创建模拟的QzoneClient"""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    client.publish_post = AsyncMock(return_value=type('obj', (object,), {'success': True, 'tid': 'published_tid', 'message': '发布成功'}))
    return client


@pytest.mark.asyncio
async def test_draft_repository_create():
    draft_data = {
        "id": str(uuid.uuid4()),
        "title": "测试草稿标题",
        "content": "测试草稿内容",
        "images": json.dumps(["https://example.com/img1.jpg", "https://example.com/img2.jpg"]),
        "status": "draft"
    }
    
    draft = await DraftRepository.create(draft_data)
    
    assert draft.id == draft_data["id"]
    assert draft.title == "测试草稿标题"
    assert draft.content == "测试草稿内容"
    assert draft.images == draft_data["images"]
    assert draft.status == "draft"


@pytest.mark.asyncio
async def test_draft_repository_get_by_id():
    draft_id = str(uuid.uuid4())
    draft_data = {
        "id": draft_id,
        "title": "获取测试标题",
        "content": "获取测试内容"
    }
    await DraftRepository.create(draft_data)
    
    draft = await DraftRepository.get_by_id(draft_id)
    
    assert draft is not None
    assert draft.id == draft_id
    assert draft.title == "获取测试标题"
    assert draft.content == "获取测试内容"


@pytest.mark.asyncio
async def test_draft_repository_get_by_id_not_found():
    draft = await DraftRepository.get_by_id(str(uuid.uuid4()))
    
    assert draft is None


@pytest.mark.asyncio
async def test_draft_repository_update():
    draft_id = str(uuid.uuid4())
    draft_data = {
        "id": draft_id,
        "title": "更新前标题",
        "content": "更新前内容"
    }
    await DraftRepository.create(draft_data)
    
    updated = await DraftRepository.update(draft_id, {
        "title": "更新后标题",
        "content": "更新后内容"
    })
    
    assert updated is not None
    assert updated.title == "更新后标题"
    assert updated.content == "更新后内容"


@pytest.mark.asyncio
async def test_draft_repository_delete_hard():
    draft_id = str(uuid.uuid4())
    draft_data = {
        "id": draft_id,
        "title": "硬删除测试",
        "content": "硬删除内容"
    }
    await DraftRepository.create(draft_data)
    
    exists_before = await DraftRepository.exists(draft_id)
    assert exists_before is True
    
    success = await DraftRepository.delete(draft_id)
    assert success is True
    
    exists_after = await DraftRepository.exists(draft_id)
    assert exists_after is False


@pytest.mark.asyncio
async def test_draft_repository_soft_delete():
    draft_id = str(uuid.uuid4())
    draft_data = {
        "id": draft_id,
        "title": "软删除测试",
        "content": "软删除内容"
    }
    await DraftRepository.create(draft_data)
    
    exists_before = await DraftRepository.exists(draft_id)
    assert exists_before is True
    
    success = await DraftRepository.soft_delete(draft_id)
    assert success is True
    
    draft = await DraftRepository.get_by_id(draft_id)
    assert draft is not None
    assert draft.status == "deleted"


@pytest.mark.asyncio
async def test_draft_repository_get_all_with_status():
    for i in range(3):
        draft_data = {
            "id": str(uuid.uuid4()),
            "title": f"草稿{i}",
            "content": f"内容{i}",
            "status": "draft" if i < 2 else "published"
        }
        await DraftRepository.create(draft_data)
    
    drafts = await DraftRepository.get_all(status="draft", limit=10, offset=0)
    
    assert len(drafts) == 2
    for draft in drafts:
        assert draft.status == "draft"


@pytest.mark.asyncio
async def test_draft_repository_count():
    for i in range(5):
        draft_data = {
            "id": str(uuid.uuid4()),
            "title": f"计数草稿{i}",
            "content": f"内容{i}"
        }
        await DraftRepository.create(draft_data)
    
    count = await DraftRepository.count()
    
    assert count >= 5


@pytest.mark.asyncio
async def test_draft_service_create_draft():
    service = DraftService()
    
    draft = await service.create_draft(
        content="服务创建测试内容",
        title="服务创建测试标题",
        images=["https://example.com/img.jpg"]
    )
    
    assert "id" in draft
    assert draft["title"] == "服务创建测试标题"
    assert draft["content"] == "服务创建测试内容"
    assert draft["images"] == ["https://example.com/img.jpg"]
    assert draft["status"] == "draft"


@pytest.mark.asyncio
async def test_draft_service_create_draft_without_images():
    service = DraftService()
    
    draft = await service.create_draft(
        content="无图片草稿内容",
        title="无图片标题"
    )
    
    assert "id" in draft
    assert draft["images"] is None
    assert draft["status"] == "draft"


@pytest.mark.asyncio
async def test_draft_service_get_draft():
    service = DraftService()
    
    created = await service.create_draft(
        content="获取测试内容",
        title="获取测试标题"
    )
    
    retrieved = await service.get_draft(created["id"])
    
    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["title"] == "获取测试标题"
    assert retrieved["content"] == "获取测试内容"


@pytest.mark.asyncio
async def test_draft_service_get_draft_not_found():
    service = DraftService()
    
    retrieved = await service.get_draft(str(uuid.uuid4()))
    
    assert retrieved is None


@pytest.mark.asyncio
async def test_draft_service_update_draft():
    service = DraftService()
    
    created = await service.create_draft(
        content="原始内容",
        title="原始标题"
    )
    
    updated = await service.update_draft(
        draft_id=created["id"],
        content="更新内容",
        title="更新标题",
        images=["https://example.com/new_img.jpg"]
    )
    
    assert updated is not None
    assert updated["id"] == created["id"]
    assert updated["title"] == "更新标题"
    assert updated["content"] == "更新内容"
    assert updated["images"] == ["https://example.com/new_img.jpg"]


@pytest.mark.asyncio
async def test_draft_service_update_draft_partial():
    service = DraftService()
    
    created = await service.create_draft(
        content="原始内容",
        title="原始标题"
    )
    
    updated = await service.update_draft(
        draft_id=created["id"],
        content="只更新内容"
    )
    
    assert updated is not None
    assert updated["content"] == "只更新内容"
    assert updated["title"] == "原始标题"


@pytest.mark.asyncio
async def test_draft_service_update_nonexistent():
    service = DraftService()
    
    updated = await service.update_draft(
        draft_id=str(uuid.uuid4()),
        content="更新不存在的草稿"
    )
    
    assert updated is None


@pytest.mark.asyncio
async def test_draft_service_delete_draft():
    service = DraftService()
    
    created = await service.create_draft(
        content="要删除的草稿",
        title="删除测试"
    )
    
    success = await service.delete_draft(created["id"], hard_delete=True)
    
    assert success is True
    
    retrieved = await service.get_draft(created["id"])
    assert retrieved is None


@pytest.mark.asyncio
async def test_draft_service_soft_delete_draft():
    service = DraftService()
    
    created = await service.create_draft(
        content="软删除测试",
        title="软删除标题"
    )
    
    success = await service.delete_draft(created["id"], hard_delete=False)
    
    assert success is True
    
    retrieved = await service.get_draft(created["id"])
    assert retrieved is not None
    assert retrieved["status"] == "deleted"


@pytest.mark.asyncio
async def test_draft_service_save_draft_new():
    service = DraftService()
    
    draft = await service.save_draft(
        draft_id=None,
        content="保存新草稿内容",
        title="保存新草稿标题"
    )
    
    assert "id" in draft
    assert draft["title"] == "保存新草稿标题"
    assert draft["content"] == "保存新草稿内容"


@pytest.mark.asyncio
async def test_draft_service_save_draft_existing():
    service = DraftService()
    
    created = await service.create_draft(
        content="原始内容",
        title="原始标题"
    )
    
    saved = await service.save_draft(
        draft_id=created["id"],
        content="保存更新内容",
        title="保存更新标题"
    )
    
    assert saved["id"] == created["id"]
    assert saved["title"] == "保存更新标题"
    assert saved["content"] == "保存更新内容"


@pytest.mark.asyncio
async def test_draft_service_publish_draft(mock_qzone_client):
    service = DraftService(mock_qzone_client)
    
    created = await service.create_draft(
        content="要发布的草稿",
        title="发布测试"
    )
    
    result = await service.publish_draft(created["id"])
    
    assert result["success"] is True
    assert result["tid"] == "published_tid"
    assert result["message"] == "发布成功"
    
    draft = await service.get_draft(created["id"])
    assert draft["status"] == "published"


@pytest.mark.asyncio
async def test_draft_service_publish_draft_not_found():
    service = DraftService()
    
    result = await service.publish_draft(str(uuid.uuid4()))
    
    assert result["success"] is False
    assert result["message"] == "草稿不存在"


@pytest.mark.asyncio
async def test_draft_service_publish_draft_already_published(mock_qzone_client):
    service = DraftService(mock_qzone_client)
    
    created = await service.create_draft(
        content="已发布草稿",
        title="已发布"
    )
    
    await service.publish_draft(created["id"])
    
    result = await service.publish_draft(created["id"])
    
    assert result["success"] is False
    assert result["message"] == "草稿已发布"


@pytest.mark.asyncio
async def test_draft_service_publish_draft_no_client():
    service = DraftService(None)
    
    created = await service.create_draft(
        content="无客户端测试",
        title="无客户端"
    )
    
    result = await service.publish_draft(created["id"])
    
    assert result["success"] is False
    assert result["message"] == "QQ空间客户端未配置，无法发布"


@pytest.mark.asyncio
async def test_draft_service_get_draft_count():
    service = DraftService()
    
    for i in range(3):
        await service.create_draft(
            content=f"计数草稿{i}",
            title=f"标题{i}"
        )
    
    count = await service.get_draft_count()
    
    assert count >= 3


@pytest.mark.asyncio
async def test_draft_service_preview_draft():
    service = DraftService()
    
    created = await service.create_draft(
        content="这是一段很长的草稿内容，用于测试预览功能，看看是否能够正确截断显示前200个字符。" * 5,
        title="预览测试标题",
        images=["img1.jpg", "img2.jpg"]
    )
    
    preview = await service.preview_draft(created["id"])
    
    assert preview is not None
    assert preview["draft_id"] == created["id"]
    assert preview["title"] == "预览测试标题"
    assert len(preview["content_preview"]) <= 200
    assert preview["content_length"] > 200
    assert preview["image_count"] == 2
    assert "created_at" in preview
    assert "updated_at" in preview
    assert preview["status"] == "draft"


@pytest.mark.asyncio
async def test_draft_service_preview_short_content():
    service = DraftService()
    
    created = await service.create_draft(
        content="短内容",
        title="短内容测试"
    )
    
    preview = await service.preview_draft(created["id"])
    
    assert preview["content_preview"] == "短内容"
    assert preview["content_length"] == 3


@pytest.mark.asyncio
async def test_draft_service_get_drafts():
    service = DraftService()
    
    for i in range(5):
        await service.create_draft(
            content=f"列表测试{i}",
            title=f"列表标题{i}"
        )
    
    drafts = await service.get_drafts(limit=3, offset=0)
    
    assert len(drafts) == 3
    
    drafts_all = await service.get_drafts(limit=10, offset=0)
    assert len(drafts_all) >= 5


@pytest.mark.asyncio
async def test_draft_service_get_drafts_filter_by_status():
    service = DraftService()
    
    await service.create_draft(content="草稿1", title="标题1")
    await service.create_draft(content="草稿2", title="标题2")
    
    draft3 = await service.create_draft(content="已发布", title="已发布标题")
    await DraftRepository.update(draft3["id"], {"status": "published"})
    
    draft4 = await service.create_draft(content="已删除", title="已删除标题")
    await DraftRepository.update(draft4["id"], {"status": "deleted"})
    
    drafts = await service.get_drafts(status="draft")
    
    assert len(drafts) == 2
    for draft in drafts:
        assert draft["status"] == "draft"
