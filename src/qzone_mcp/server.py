import asyncio
import json
import logging
import signal
import sys
from typing import List, Optional

import aiohttp

from fastmcp import FastMCP
from fastmcp.tools.base import ToolResult
from mcp.types import ToolAnnotations

from .api.session import QzoneSession, LoginExpiredError, CookieParseError
from .api.client import QzoneClient
from .api.model import Feed as FeedModel
from .config import config
from .db.manager import db_manager
from .db.repository import FeedRepository, CommentRepository
from .draft.service import DraftService

logging.basicConfig(level=config.log_level)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="qzone",
    instructions="""QQ空间操作工具集 - 提供完整的QQ空间功能支持

**功能特性：**
- 获取说说列表和详情
- 发布新说说
- 点赞和评论说说
- 获取访客记录
- 本地数据库存储（持久化保存说说和评论）
- 草稿箱功能（创建、编辑、保存、发布草稿）

**使用前请确保：**
1. 通过 qzone_set_cookie 工具设置有效的QQ空间Cookie
2. 或配置OneBot客户端自动获取Cookie

**注意事项：**
- 所有操作需要有效的登录状态
- 敏感操作（发布、点赞、评论）请谨慎使用
- 建议先使用 qzone_login_status 检查登录状态
- 数据库存储功能无需登录即可使用""",
    version="1.0.0"
)

session = QzoneSession(config)
client = QzoneClient(session)
draft_service = DraftService(client)

shutdown_event = asyncio.Event()


async def cleanup_resources():
    logger.info("开始清理资源...")
    
    await client.close()
    logger.info("HTTP 会话已关闭")
    
    await db_manager.close()
    logger.info("数据库连接已关闭")
    
    logger.info("资源清理完成")


def signal_handler(signum, frame):
    logger.info(f"收到信号 {signum}，准备优雅退出...")
    shutdown_event.set()


@mcp.tool(
    name="qzone_get_feeds",
    description="获取QQ空间说说列表",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_feeds(
    user_id: Optional[str] = None,
    pos: int = 0,
    num: int = 5,
    with_detail: bool = False
) -> ToolResult:
    """
    获取QQ空间说说列表
    
    Args:
        user_id: 目标用户QQ号，默认为当前登录用户
        pos: 起始位置，用于分页，从0开始
        num: 获取数量，建议不超过20
        with_detail: 是否包含完整评论列表
    
    Returns:
        说说列表，包含作者信息、内容、点赞数、评论数等
    
    Example:
        {
            "result": [
                {
                    "tid": "123456789",
                    "uin": 123456789,
                    "nickname": "张三",
                    "content": "今天天气真好！",
                    "likes": 10,
                    "comments": 3,
                    "time": "2024-01-15 10:30"
                }
            ]
        }
    """
    try:
        if num < 1 or num > 50:
            return ToolResult(content="参数错误：num 必须在 1-50 之间")
        
        feeds = await client.get_feeds(user_id, pos, num, with_detail)
        return ToolResult(structured_content={"result": [f.model_dump() for f in feeds]})
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"获取说说失败: {e}")
        return ToolResult(content=f"获取说说失败：{str(e)}")


@mcp.tool(
    name="qzone_get_post_detail",
    description="获取单条说说详情",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_post_detail(
    tid: str,
    author_uin: int
) -> ToolResult:
    """
    获取单条说说的完整详情，包含所有评论
    
    Args:
        tid: 说说ID（必填）
        author_uin: 作者QQ号（必填）
    
    Returns:
        说说详情，包含完整评论列表
    
    Example:
        {
            "result": {
                "tid": "123456789",
                "uin": 123456789,
                "nickname": "张三",
                "content": "今天天气真好！",
                "likes": 10,
                "comments": 3,
                "comment_list": [
                    {"id": "c1", "uin": 987654321, "nickname": "李四", "content": "确实不错！"}
                ]
            }
        }
    """
    try:
        if not tid or not author_uin:
            return ToolResult(content="参数错误：tid 和 author_uin 均为必填参数")
        
        feed = await client.get_post_detail(tid, author_uin)
        return ToolResult(structured_content={"result": feed.model_dump()})
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"获取说说详情失败: {e}")
        return ToolResult(content=f"获取说说详情失败：{str(e)}")


@mcp.tool(
    name="qzone_publish_post",
    description="发布QQ空间说说",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_publish_post(
    text: str,
    image_urls: Optional[List[str]] = None
) -> ToolResult:
    """
    在QQ空间发布新说说
    
    Args:
        text: 说说内容（必填），最大长度建议不超过2000字
        image_urls: 图片URL列表，可选，最多支持9张图片
    
    Returns:
        发布结果，包含说说ID和状态信息
    
    Example:
        {
            "result": {
                "success": true,
                "tid": "123456789",
                "message": "发布成功"
            }
        }
    """
    try:
        if not text or not text.strip():
            return ToolResult(content="参数错误：说说内容不能为空")
        
        if len(text) > 2000:
            return ToolResult(content="参数错误：说说内容超过最大长度限制（2000字）")
        
        if image_urls and len(image_urls) > 9:
            return ToolResult(content="参数错误：最多支持9张图片")
        
        result = await client.publish_post(text.strip(), image_urls or [])
        if result.success:
            return ToolResult(structured_content={"result": result.model_dump()})
        return ToolResult(content=f"发布失败：{result.message}")
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"发布说说失败: {e}")
        return ToolResult(content=f"发布说说失败：{str(e)}")


@mcp.tool(
    name="qzone_like_post",
    description="点赞说说",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_like_post(
    tid: str,
    author_uin: int
) -> ToolResult:
    """
    为指定说说点赞
    
    Args:
        tid: 说说ID（必填）
        author_uin: 作者QQ号（必填）
    
    Returns:
        点赞结果
    
    Example:
        {
            "result": {
                "success": true,
                "message": "点赞成功"
            }
        }
    """
    try:
        if not tid or not author_uin:
            return ToolResult(content="参数错误：tid 和 author_uin 均为必填参数")
        
        result = await client.like_post(tid, author_uin)
        if result.success:
            return ToolResult(structured_content={"result": result.model_dump()})
        return ToolResult(content=f"点赞失败：{result.message}")
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"点赞失败: {e}")
        return ToolResult(content=f"点赞失败：{str(e)}")


@mcp.tool(
    name="qzone_comment_post",
    description="评论说说",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_comment_post(
    tid: str,
    author_uin: int,
    content: str
) -> ToolResult:
    """
    对指定说说发表评论
    
    Args:
        tid: 说说ID（必填）
        author_uin: 作者QQ号（必填）
        content: 评论内容（必填），最大长度建议不超过500字
    
    Returns:
        评论结果，包含评论ID
    
    Example:
        {
            "result": {
                "success": true,
                "comment_id": "c123456",
                "message": "评论成功"
            }
        }
    """
    try:
        if not tid or not author_uin or not content:
            return ToolResult(content="参数错误：tid、author_uin 和 content 均为必填参数")
        
        if len(content) > 500:
            return ToolResult(content="参数错误：评论内容超过最大长度限制（500字）")
        
        result = await client.comment_post(tid, author_uin, content.strip())
        if result.success:
            return ToolResult(structured_content={"result": result.model_dump()})
        return ToolResult(content=f"评论失败：{result.message}")
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"评论失败: {e}")
        return ToolResult(content=f"评论失败：{str(e)}")


@mcp.tool(
    name="qzone_reply_comment",
    description="回复评论",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_reply_comment(
    tid: str,
    author_uin: int,
    comment_id: str,
    content: str
) -> ToolResult:
    """
    回复指定说说下的评论
    
    Args:
        tid: 说说ID（必填）
        author_uin: 作者QQ号（必填）
        comment_id: 要回复的评论ID（必填）
        content: 回复内容（必填），最大长度建议不超过500字
    
    Returns:
        回复结果，包含回复ID
    
    Example:
        {
            "result": {
                "success": true,
                "comment_id": "r123456",
                "message": "回复成功"
            }
        }
    """
    try:
        if not tid or not author_uin or not comment_id or not content:
            return ToolResult(content="参数错误：tid、author_uin、comment_id 和 content 均为必填参数")
        
        if len(content) > 500:
            return ToolResult(content="参数错误：回复内容超过最大长度限制（500字）")
        
        result = await client.reply_comment(tid, author_uin, comment_id, content.strip())
        if result.success:
            return ToolResult(structured_content={"result": result.model_dump()})
        return ToolResult(content=f"回复失败：{result.message}")
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"回复评论失败: {e}")
        return ToolResult(content=f"回复评论失败：{str(e)}")


@mcp.tool(
    name="qzone_get_visitors",
    description="获取访客记录",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_visitors(
    page: int = 1,
    num: int = 20
) -> ToolResult:
    """
    获取QQ空间访客记录
    
    Args:
        page: 页码，从1开始
        num: 每页数量，建议不超过50
    
    Returns:
        访客列表，包含访客昵称、QQ号和访问时间
    
    Example:
        {
            "result": [
                {
                    "uin": 987654321,
                    "nickname": "李四",
                    "avatar": "https://q.qlogo.cn/...",
                    "time": "2024-01-15 10:30"
                }
            ]
        }
    """
    try:
        if page < 1:
            return ToolResult(content="参数错误：page 必须大于0")
        
        if num < 1 or num > 50:
            return ToolResult(content="参数错误：num 必须在 1-50 之间")
        
        visitors = await client.get_visitors(page, num)
        return ToolResult(structured_content={"result": [v.model_dump() for v in visitors]})
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"获取访客失败: {e}")
        return ToolResult(content=f"获取访客失败：{str(e)}")


@mcp.tool(
    name="qzone_set_cookie",
    description="设置QQ空间Cookie",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_set_cookie(cookie_string: str) -> ToolResult:
    """
    设置QQ空间登录Cookie，用于后续所有操作
    
    Args:
        cookie_string: QQ空间Cookie字符串（必填），需要包含uin、skey、p_skey字段
    
    Returns:
        设置结果
    
    Example:
        {
            "result": {
                "message": "Cookie设置成功"
            }
        }
    
    Tips:
        获取Cookie方法：
        1. 登录QQ空间网页版
        2. 打开开发者工具（F12）
        3. 在Application -> Cookies中复制user.qzone.qq.com的所有Cookie
    """
    try:
        if not cookie_string or not cookie_string.strip():
            return ToolResult(content="参数错误：Cookie字符串不能为空")
        
        await session.login(cookie_string)
        config.qzone.cookie = cookie_string
        return ToolResult(structured_content={"result": {"message": "Cookie设置成功"}})
    except CookieParseError:
        return ToolResult(content="Cookie解析失败：请确保Cookie包含uin、skey、p_skey字段")
    except ValueError as e:
        return ToolResult(content=f"参数错误：{str(e)}")
    except Exception as e:
        logger.error(f"设置Cookie失败: {e}")
        return ToolResult(content=f"设置Cookie失败：{str(e)}")


@mcp.tool(
    name="qzone_login_status",
    description="获取登录状态",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_login_status() -> ToolResult:
    """
    获取当前登录状态
    
    Returns:
        登录状态信息
    
    Example:
        {
            "result": {
                "logged_in": true,
                "uin": 123456789
            }
        }
    """
    try:
        is_logged_in = session.is_logged_in
        ctx = await session.get_ctx() if is_logged_in else None
        
        result = {
            "logged_in": is_logged_in,
            "uin": ctx.uin if ctx else None
        }
        return ToolResult(structured_content={"result": result})
    except LoginExpiredError:
        return ToolResult(structured_content={"result": {"logged_in": False, "uin": None}})
    except Exception as e:
        logger.error(f"获取登录状态失败: {e}")
        return ToolResult(content=f"获取登录状态失败：{str(e)}")


@mcp.tool(
    name="qzone_check_onebot_status",
    description="检查 OneBot 服务连接状态",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_check_onebot_status() -> ToolResult:
    """
    检查 MCP 服务器与 OneBot 的连通状态
    
    Returns:
        OneBot 连接状态信息
    
    Example:
        {
            "result": {
                "connected": true,
                "enabled": true,
                "provider": "llonebot",
                "host": "127.0.0.1",
                "port": 5700,
                "has_cookies": true,
                "message": "连接成功，已获取Cookie"
            }
        }
    """
    try:
        onebot_cfg = config.onebot
        
        result = {
            "enabled": onebot_cfg.enabled,
            "provider": onebot_cfg.provider,
            "host": onebot_cfg.host,
            "port": onebot_cfg.port,
            "connected": False,
            "has_cookies": False,
            "status_code": None,
            "message": ""
        }
        
        if not onebot_cfg.enabled:
            result["message"] = "OneBot 未启用"
            return ToolResult(structured_content={"result": result})
        
        url = f"http://{onebot_cfg.host}:{onebot_cfg.port}{onebot_cfg.api_path}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=onebot_cfg.timeout)) as client_session:
            async with client_session.get(url, params={"domain": "user.qzone.qq.com"}) as resp:
                result["status_code"] = resp.status
                
                if resp.status == 200:
                    data = await resp.json()
                    
                    if onebot_cfg.provider == "napcat":
                        cookies_str = data.get("data", {}).get("cookies", "")
                    elif onebot_cfg.provider == "llonebot":
                        cookies_str = data.get("data", {}).get("cookies", "")
                    else:
                        cookies_str = data.get("cookies", "")
                    
                    result["connected"] = True
                    result["has_cookies"] = bool(cookies_str)
                    result["message"] = "连接成功" + ("，已获取Cookie" if result["has_cookies"] else "，但Cookie为空")
                else:
                    result["message"] = f"连接失败，HTTP状态码: {resp.status}"
        
        return ToolResult(structured_content={"result": result})
    
    except aiohttp.ClientError as e:
        return ToolResult(structured_content={
            "result": {
                "enabled": config.onebot.enabled,
                "provider": config.onebot.provider,
                "host": config.onebot.host,
                "port": config.onebot.port,
                "connected": False,
                "has_cookies": False,
                "status_code": None,
                "message": f"连接失败: {str(e)}"
            }
        })
    except Exception as e:
        logger.error(f"检查 OneBot 状态失败: {e}")
        return ToolResult(content=f"检查 OneBot 状态失败：{str(e)}")


# ==================== 数据库相关工具 ====================

@mcp.tool(
    name="qzone_save_feed",
    description="保存说说到本地数据库",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_save_feed(
    tid: str,
    uin: int,
    content: str,
    nickname: Optional[str] = None,
    images: Optional[str] = None,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    time: Optional[str] = None,
    is_liked: bool = False
) -> ToolResult:
    """
    保存说说数据到本地数据库
    
    Args:
        tid: 说说ID（必填）
        uin: 发布者QQ号（必填）
        content: 说说内容（必填）
        nickname: 发布者昵称
        images: 图片URL列表（JSON格式）
        likes: 点赞数
        comments: 评论数
        shares: 分享数
        time: 发布时间
        is_liked: 是否已点赞
    
    Returns:
        保存结果
    
    Example:
        {
            "result": {
                "success": true,
                "message": "保存成功",
                "tid": "123456789"
            }
        }
    """
    try:
        if not tid or not uin or not content:
            return ToolResult(content="参数错误：tid、uin 和 content 均为必填参数")
        
        await db_manager.initialize()
        
        feed_data = {
            "tid": tid,
            "uin": uin,
            "content": content,
            "nickname": nickname,
            "images": images,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "time": time,
            "is_liked": is_liked
        }
        
        existing = await FeedRepository.get_by_tid(tid)
        if existing:
            await FeedRepository.update(tid, feed_data)
            return ToolResult(structured_content={"result": {"success": True, "message": "更新成功", "tid": tid}})
        
        await FeedRepository.create(feed_data)
        return ToolResult(structured_content={"result": {"success": True, "message": "保存成功", "tid": tid}})
    
    except Exception as e:
        logger.error(f"保存说说失败: {e}")
        return ToolResult(content=f"保存说说失败：{str(e)}")


@mcp.tool(
    name="qzone_save_feed_with_comments",
    description="保存说说及评论到本地数据库",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_save_feed_with_comments(
    tid: str,
    uin: int,
    content: str,
    nickname: Optional[str] = None,
    images: Optional[str] = None,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    time: Optional[str] = None,
    is_liked: bool = False,
    comment_list: Optional[str] = None
) -> ToolResult:
    """
    保存说说及其评论数据到本地数据库
    
    Args:
        tid: 说说ID（必填）
        uin: 发布者QQ号（必填）
        content: 说说内容（必填）
        nickname: 发布者昵称
        images: 图片URL列表（JSON格式）
        likes: 点赞数
        comments: 评论数
        shares: 分享数
        time: 发布时间
        is_liked: 是否已点赞
        comment_list: 评论列表（JSON格式，包含id, uin, nickname, content, time, parent_id字段）
    
    Returns:
        保存结果
    
    Example:
        {
            "result": {
                "success": true,
                "message": "保存成功",
                "tid": "123456789",
                "comment_count": 3
            }
        }
    """
    try:
        if not tid or not uin or not content:
            return ToolResult(content="参数错误：tid、uin 和 content 均为必填参数")
        
        await db_manager.initialize()
        
        feed_data = {
            "tid": tid,
            "uin": uin,
            "content": content,
            "nickname": nickname,
            "images": images,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "time": time,
            "is_liked": is_liked
        }
        
        existing = await FeedRepository.get_by_tid(tid)
        if existing:
            await FeedRepository.update(tid, feed_data)
        else:
            await FeedRepository.create(feed_data)
        
        if comment_list:
            try:
                comments_data = json.loads(comment_list)
                if isinstance(comments_data, list):
                    for comment in comments_data:
                        comment["tid"] = tid
                        comment["comment_id"] = comment.get("id", comment.get("comment_id", str(comment.get("id", ""))))
                    await CommentRepository.create_batch(comments_data)
                    comment_count = len(comments_data)
                else:
                    comment_count = 0
            except json.JSONDecodeError:
                comment_count = 0
        else:
            comment_count = 0
        
        return ToolResult(structured_content={
            "result": {
                "success": True,
                "message": "保存成功",
                "tid": tid,
                "comment_count": comment_count
            }
        })
    
    except Exception as e:
        logger.error(f"保存说说及评论失败: {e}")
        return ToolResult(content=f"保存说说及评论失败：{str(e)}")


@mcp.tool(
    name="qzone_get_saved_feeds",
    description="获取本地保存的说说列表",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_saved_feeds(
    uin: Optional[int] = None,
    limit: int = 20,
    offset: int = 0
) -> ToolResult:
    """
    获取本地数据库中保存的说说列表
    
    Args:
        uin: 发布者QQ号（可选，不传则获取所有）
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        说说列表
    
    Example:
        {
            "result": [
                {
                    "tid": "123456789",
                    "uin": 123456789,
                    "nickname": "张三",
                    "content": "今天天气真好！",
                    "likes": 10,
                    "comments": 3,
                    "time": "2024-01-15 10:30"
                }
            ],
            "total": 100
        }
    """
    try:
        await db_manager.initialize()
        
        if uin:
            feeds = await FeedRepository.get_by_uin(uin, limit=limit, offset=offset)
            total = await FeedRepository.count()
        else:
            feeds = await FeedRepository.get_all(limit=limit, offset=offset)
            total = await FeedRepository.count()
        
        return ToolResult(structured_content={
            "result": [feed.to_dict() for feed in feeds],
            "total": total
        })
    
    except Exception as e:
        logger.error(f"获取本地说说失败: {e}")
        return ToolResult(content=f"获取本地说说失败：{str(e)}")


@mcp.tool(
    name="qzone_get_saved_feed",
    description="获取单条本地保存的说说",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_saved_feed(tid: str) -> ToolResult:
    """
    根据说说ID获取本地保存的说说详情
    
    Args:
        tid: 说说ID（必填）
    
    Returns:
        说说详情，包含评论列表
    
    Example:
        {
            "result": {
                "tid": "123456789",
                "uin": 123456789,
                "nickname": "张三",
                "content": "今天天气真好！",
                "comments": [
                    {"comment_id": "c1", "uin": 987654321, "nickname": "李四", "content": "确实不错！"}
                ]
            }
        }
    """
    try:
        if not tid:
            return ToolResult(content="参数错误：tid 为必填参数")
        
        await db_manager.initialize()
        
        feed = await FeedRepository.get_by_tid(tid)
        if not feed:
            return ToolResult(content="说说不存在")
        
        comments = await CommentRepository.get_by_tid(tid)
        
        result = feed.to_dict()
        result["comments"] = [comment.to_dict() for comment in comments]
        
        return ToolResult(structured_content={"result": result})
    
    except Exception as e:
        logger.error(f"获取本地说说详情失败: {e}")
        return ToolResult(content=f"获取本地说说详情失败：{str(e)}")


@mcp.tool(
    name="qzone_delete_saved_feed",
    description="删除本地保存的说说",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_delete_saved_feed(tid: str) -> ToolResult:
    """
    删除本地数据库中保存的说说（级联删除关联评论）
    
    Args:
        tid: 说说ID（必填）
    
    Returns:
        删除结果
    
    Example:
        {
            "result": {
                "success": true,
                "message": "删除成功"
            }
        }
    """
    try:
        if not tid:
            return ToolResult(content="参数错误：tid 为必填参数")
        
        await db_manager.initialize()
        
        success = await FeedRepository.delete(tid)
        
        if success:
            return ToolResult(structured_content={"result": {"success": True, "message": "删除成功"}})
        else:
            return ToolResult(content="说说不存在")
    
    except Exception as e:
        logger.error(f"删除本地说说失败: {e}")
        return ToolResult(content=f"删除本地说说失败：{str(e)}")


@mcp.tool(
    name="qzone_get_saved_feed_count",
    description="获取本地保存的说说数量",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_saved_feed_count() -> ToolResult:
    """
    获取本地数据库中保存的说说总数
    
    Returns:
        说说数量
    
    Example:
        {
            "result": {
                "count": 100
            }
        }
    """
    try:
        await db_manager.initialize()
        
        count = await FeedRepository.count()
        
        return ToolResult(structured_content={"result": {"count": count}})
    
    except Exception as e:
        logger.error(f"获取说说数量失败: {e}")
        return ToolResult(content=f"获取说说数量失败：{str(e)}")


# ==================== 草稿箱相关工具 ====================

@mcp.tool(
    name="qzone_create_draft",
    description="创建新草稿",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_create_draft(
    content: str,
    title: Optional[str] = None,
    images: Optional[str] = None
) -> ToolResult:
    """
    创建新的说说草稿
    
    Args:
        content: 草稿内容（必填）
        title: 草稿标题（可选）
        images: 图片URL列表（JSON格式，可选）
    
    Returns:
        草稿信息
    
    Example:
        {
            "result": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "我的草稿",
                "content": "今天天气真好！",
                "status": "draft",
                "created_at": "2024-01-15T10:30:00"
            }
        }
    """
    try:
        if not content or not content.strip():
            return ToolResult(content="参数错误：草稿内容不能为空")
        
        await db_manager.initialize()
        
        images_list = None
        if images:
            try:
                images_list = json.loads(images)
                if not isinstance(images_list, list):
                    images_list = None
            except json.JSONDecodeError:
                images_list = None
        
        draft = await draft_service.create_draft(content.strip(), title, images_list)
        
        return ToolResult(structured_content={"result": draft})
    
    except Exception as e:
        logger.error(f"创建草稿失败: {e}")
        return ToolResult(content=f"创建草稿失败：{str(e)}")


@mcp.tool(
    name="qzone_update_draft",
    description="更新草稿内容",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_update_draft(
    draft_id: str,
    content: Optional[str] = None,
    title: Optional[str] = None,
    images: Optional[str] = None
) -> ToolResult:
    """
    更新现有草稿的内容
    
    Args:
        draft_id: 草稿ID（必填）
        content: 新内容（可选）
        title: 新标题（可选）
        images: 新图片URL列表（JSON格式，可选）
    
    Returns:
        更新后的草稿信息
    
    Example:
        {
            "result": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "修改后的标题",
                "content": "修改后的内容",
                "updated_at": "2024-01-15T10:35:00"
            }
        }
    """
    try:
        if not draft_id:
            return ToolResult(content="参数错误：draft_id 为必填参数")
        
        if content is None and title is None and images is None:
            return ToolResult(content="参数错误：至少需要提供 content、title 或 images 中的一个")
        
        await db_manager.initialize()
        
        images_list = None
        if images is not None:
            try:
                images_list = json.loads(images)
                if not isinstance(images_list, list):
                    images_list = None
            except json.JSONDecodeError:
                images_list = None
        
        draft = await draft_service.update_draft(draft_id, content, title, images_list)
        
        if draft:
            return ToolResult(structured_content={"result": draft})
        else:
            return ToolResult(content="草稿不存在")
    
    except Exception as e:
        logger.error(f"更新草稿失败: {e}")
        return ToolResult(content=f"更新草稿失败：{str(e)}")


@mcp.tool(
    name="qzone_get_draft",
    description="获取草稿详情",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_draft(draft_id: str) -> ToolResult:
    """
    获取指定草稿的详细信息
    
    Args:
        draft_id: 草稿ID（必填）
    
    Returns:
        草稿详情
    
    Example:
        {
            "result": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "我的草稿",
                "content": "今天天气真好！",
                "images": ["https://example.com/img.jpg"],
                "status": "draft",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    """
    try:
        if not draft_id:
            return ToolResult(content="参数错误：draft_id 为必填参数")
        
        await db_manager.initialize()
        
        draft = await draft_service.get_draft(draft_id)
        
        if draft:
            return ToolResult(structured_content={"result": draft})
        else:
            return ToolResult(content="草稿不存在")
    
    except Exception as e:
        logger.error(f"获取草稿失败: {e}")
        return ToolResult(content=f"获取草稿失败：{str(e)}")


@mcp.tool(
    name="qzone_get_drafts",
    description="获取草稿列表",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_drafts(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> ToolResult:
    """
    获取草稿列表
    
    Args:
        status: 状态过滤（可选），可选值：draft/published/deleted
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        草稿列表
    
    Example:
        {
            "result": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "我的草稿",
                    "content": "今天天气真好！",
                    "status": "draft"
                }
            ],
            "total": 5
        }
    """
    try:
        await db_manager.initialize()
        
        drafts = await draft_service.get_drafts(status=status, limit=limit, offset=offset)
        total = await draft_service.get_draft_count(status=status)
        
        return ToolResult(structured_content={"result": drafts, "total": total})
    
    except Exception as e:
        logger.error(f"获取草稿列表失败: {e}")
        return ToolResult(content=f"获取草稿列表失败：{str(e)}")


@mcp.tool(
    name="qzone_delete_draft",
    description="删除草稿",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_delete_draft(
    draft_id: str,
    hard_delete: bool = False
) -> ToolResult:
    """
    删除草稿（默认软删除，可选择硬删除）
    
    Args:
        draft_id: 草稿ID（必填）
        hard_delete: 是否硬删除（可选，默认False即软删除）
    
    Returns:
        删除结果
    
    Example:
        {
            "result": {
                "success": true,
                "message": "删除成功"
            }
        }
    """
    try:
        if not draft_id:
            return ToolResult(content="参数错误：draft_id 为必填参数")
        
        await db_manager.initialize()
        
        success = await draft_service.delete_draft(draft_id, hard_delete)
        
        if success:
            return ToolResult(structured_content={"result": {"success": True, "message": "删除成功"}})
        else:
            return ToolResult(content="草稿不存在")
    
    except Exception as e:
        logger.error(f"删除草稿失败: {e}")
        return ToolResult(content=f"删除草稿失败：{str(e)}")


@mcp.tool(
    name="qzone_preview_draft",
    description="预览草稿",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_preview_draft(draft_id: str) -> ToolResult:
    """
    预览草稿内容（包含内容预览、长度统计等）
    
    Args:
        draft_id: 草稿ID（必填）
    
    Returns:
        草稿预览信息
    
    Example:
        {
            "result": {
                "draft_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "我的草稿",
                "content_preview": "今天天气真好！",
                "content_length": 8,
                "image_count": 0,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
                "status": "draft"
            }
        }
    """
    try:
        if not draft_id:
            return ToolResult(content="参数错误：draft_id 为必填参数")
        
        await db_manager.initialize()
        
        preview = await draft_service.preview_draft(draft_id)
        
        if preview:
            return ToolResult(structured_content={"result": preview})
        else:
            return ToolResult(content="草稿不存在")
    
    except Exception as e:
        logger.error(f"预览草稿失败: {e}")
        return ToolResult(content=f"预览草稿失败：{str(e)}")


@mcp.tool(
    name="qzone_publish_draft",
    description="发布草稿为说说",
    annotations=ToolAnnotations(readOnlyHint=False)
)
async def qzone_publish_draft(draft_id: str) -> ToolResult:
    """
    将草稿发布为QQ空间说说
    
    Args:
        draft_id: 草稿ID（必填）
    
    Returns:
        发布结果
    
    Example:
        {
            "result": {
                "success": true,
                "tid": "123456789",
                "message": "发布成功"
            }
        }
    """
    try:
        if not draft_id:
            return ToolResult(content="参数错误：draft_id 为必填参数")
        
        await db_manager.initialize()
        
        result = await draft_service.publish_draft(draft_id)
        
        return ToolResult(structured_content={"result": result})
    
    except LoginExpiredError:
        return ToolResult(content="登录失效，请使用 qzone_set_cookie 工具重新设置Cookie")
    except Exception as e:
        logger.error(f"发布草稿失败: {e}")
        return ToolResult(content=f"发布草稿失败：{str(e)}")


@mcp.tool(
    name="qzone_get_draft_count",
    description="获取草稿数量",
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def qzone_get_draft_count(status: Optional[str] = None) -> ToolResult:
    """
    获取草稿数量
    
    Args:
        status: 状态过滤（可选），可选值：draft/published/deleted
    
    Returns:
        草稿数量
    
    Example:
        {
            "result": {
                "count": 5
            }
        }
    """
    try:
        await db_manager.initialize()
        
        count = await draft_service.get_draft_count(status=status)
        
        return ToolResult(structured_content={"result": {"count": count}})
    
    except Exception as e:
        logger.error(f"获取草稿数量失败: {e}")
        return ToolResult(content=f"获取草稿数量失败：{str(e)}")


async def run_server():
    await db_manager.initialize()
    logger.info("数据库初始化完成")
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("QQ空间 MCP 服务器启动")
    
    mcp_task = asyncio.create_task(mcp.run_async())
    
    await shutdown_event.wait()
    
    logger.info("开始优雅退出...")
    
    mcp_task.cancel()
    try:
        await mcp_task
    except asyncio.CancelledError:
        logger.info("MCP 服务器任务已取消")
    
    await cleanup_resources()
    
    logger.info("服务器已优雅退出")
    sys.exit(0)


def main():
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
