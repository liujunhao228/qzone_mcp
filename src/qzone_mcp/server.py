import asyncio
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
from .config import config

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

**使用前请确保：**
1. 通过 qzone_set_cookie 工具设置有效的QQ空间Cookie
2. 或配置OneBot客户端自动获取Cookie

**注意事项：**
- 所有操作需要有效的登录状态
- 敏感操作（发布、点赞、评论）请谨慎使用
- 建议先使用 qzone_login_status 检查登录状态""",
    version="1.0.0"
)

session = QzoneSession(config)
client = QzoneClient(session)

shutdown_event = asyncio.Event()


async def cleanup_resources():
    logger.info("开始清理资源...")
    
    await client.close()
    logger.info("HTTP 会话已关闭")
    
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
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=onebot_cfg.timeout)) as client:
            async with client.get(url, params={"domain": "user.qzone.qq.com"}) as resp:
                result["status_code"] = resp.status
                
                if resp.status == 200:
                    data = await resp.json()
                    
                    if onebot_cfg.provider == "napcat":
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


async def run_server():
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