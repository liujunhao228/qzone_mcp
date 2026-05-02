import json
import uuid
from typing import Optional, List, Dict, Any

from ..api.client import QzoneClient
from ..db.repository import DraftRepository, FeedRepository


class DraftService:
    """草稿箱服务 - 提供草稿管理的业务逻辑"""
    
    def __init__(self, qzone_client: Optional[QzoneClient] = None):
        """
        初始化草稿箱服务
        
        Args:
            qzone_client: QzoneClient实例，用于发布草稿时调用QQ空间API
        """
        self.qzone_client = qzone_client
    
    async def create_draft(self, content: str, title: Optional[str] = None, images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        创建新草稿
        
        Args:
            content: 草稿内容
            title: 草稿标题（可选）
            images: 图片URL列表（可选）
        
        Returns:
            草稿信息字典
        """
        draft_id = str(uuid.uuid4())
        images_json = json.dumps(images) if images else None
        
        draft = await DraftRepository.create({
            "id": draft_id,
            "title": title,
            "content": content,
            "images": images_json,
            "status": "draft"
        })
        
        result = draft.to_dict()
        if draft.images:
            result["images"] = json.loads(draft.images)
        return result
    
    async def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        获取草稿详情
        
        Args:
            draft_id: 草稿ID
        
        Returns:
            草稿信息字典，如果不存在返回None
        """
        draft = await DraftRepository.get_by_id(draft_id)
        if draft:
            result = draft.to_dict()
            if draft.images:
                result["images"] = json.loads(draft.images)
            return result
        return None
    
    async def get_drafts(self, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取草稿列表
        
        Args:
            status: 草稿状态过滤（可选），可选值：draft/published/deleted
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            草稿信息字典列表
        """
        drafts = await DraftRepository.get_all(status=status, limit=limit, offset=offset)
        
        result = []
        for draft in drafts:
            draft_dict = draft.to_dict()
            if draft.images:
                draft_dict["images"] = json.loads(draft.images)
            result.append(draft_dict)
        
        return result
    
    async def update_draft(self, draft_id: str, content: Optional[str] = None, title: Optional[str] = None, images: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        更新草稿内容
        
        Args:
            draft_id: 草稿ID
            content: 新内容（可选）
            title: 新标题（可选）
            images: 新图片URL列表（可选）
        
        Returns:
            更新后的草稿信息字典，如果不存在返回None
        """
        update_data: Dict[str, Any] = {}
        
        if content is not None:
            update_data["content"] = content
        
        if title is not None:
            update_data["title"] = title
        
        if images is not None:
            update_data["images"] = json.dumps(images)
        
        if not update_data:
            return await self.get_draft(draft_id)
        
        draft = await DraftRepository.update(draft_id, update_data)
        if draft:
            result = draft.to_dict()
            if draft.images:
                result["images"] = json.loads(draft.images)
            return result
        return None
    
    async def delete_draft(self, draft_id: str, hard_delete: bool = False) -> bool:
        """
        删除草稿
        
        Args:
            draft_id: 草稿ID
            hard_delete: 是否硬删除（True=直接删除，False=软删除标记）
        
        Returns:
            是否删除成功
        """
        if hard_delete:
            return await DraftRepository.delete(draft_id)
        else:
            return await DraftRepository.soft_delete(draft_id)
    
    async def save_draft(self, draft_id: str, content: str, title: Optional[str] = None, images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        保存草稿（存在则更新，不存在则创建）
        
        Args:
            draft_id: 草稿ID（如果为None或空则创建新草稿）
            content: 草稿内容
            title: 草稿标题（可选）
            images: 图片URL列表（可选）
        
        Returns:
            草稿信息字典
        """
        if draft_id and await DraftRepository.exists(draft_id):
            result = await self.update_draft(draft_id, content, title, images)
            if result:
                return result
        
        return await self.create_draft(content, title, images)
    
    async def publish_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        发布草稿为说说
        
        Args:
            draft_id: 草稿ID
        
        Returns:
            发布结果字典
        """
        draft = await DraftRepository.get_by_id(draft_id)
        
        if not draft:
            return {
                "success": False,
                "message": "草稿不存在"
            }
        
        if draft.status == "published":
            return {
                "success": False,
                "message": "草稿已发布"
            }
        
        if not self.qzone_client:
            return {
                "success": False,
                "message": "QQ空间客户端未配置，无法发布"
            }
        
        try:
            images = json.loads(draft.images) if draft.images else []
            result = await self.qzone_client.publish_post(draft.content, images)
            
            if result.success:
                await DraftRepository.update(draft_id, {"status": "published"})
                return {
                    "success": True,
                    "tid": result.tid,
                    "message": "发布成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"发布失败: {result.message}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"发布异常: {str(e)}"
            }
    
    async def get_draft_count(self, status: Optional[str] = None) -> int:
        """
        获取草稿数量
        
        Args:
            status: 草稿状态过滤（可选）
        
        Returns:
            草稿数量
        """
        return await DraftRepository.count(status=status)
    
    async def preview_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        预览草稿（返回格式化的预览内容）
        
        Args:
            draft_id: 草稿ID
        
        Returns:
            预览信息字典
        """
        draft = await self.get_draft(draft_id)
        
        if not draft:
            return None
        
        images = draft.get("images") or []
        return {
            "draft_id": draft["id"],
            "title": draft["title"] or "无标题",
            "content_preview": draft["content"][:197] + "..." if len(draft["content"]) > 200 else draft["content"],
            "content_length": len(draft["content"]),
            "image_count": len(images),
            "created_at": draft["created_at"],
            "updated_at": draft["updated_at"],
            "status": draft["status"]
        }
