import asyncio
import json
from typing import Optional, List

import typer

from .api.session import QzoneSession
from .api.client import QzoneHttpClient
from .api.qzone_api import QzoneAPI
from .adapters.llm import create_llm_adapter
from .config import config

app = typer.Typer(name="qzone-cli", help="QQ空间命令行工具")

session = QzoneSession(config)
http_client = QzoneHttpClient(session, config)
api = QzoneAPI(http_client)
llm = create_llm_adapter(config)


@app.command("feeds", help="获取说说列表")
def get_feeds(
    user: Optional[str] = typer.Option(None, "--user", "-u", help="目标QQ号"),
    num: int = typer.Option(5, "--num", "-n", help="获取数量"),
    detail: bool = typer.Option(False, "--detail", "-d", help="获取详情")
):
    try:
        async def fetch_feeds():
            from .model import Feed
            resp = await api.get_feeds(user or "", pos=0, num=num, with_detail=detail)
            if resp.ok:
                feeds_data = resp.data.get("feeds", [])
                return [Feed(**feed) for feed in feeds_data]
            return []
        
        feeds = asyncio.run(fetch_feeds())
        for i, feed in enumerate(feeds, 1):
            print(f"\n=== 说说 {i} ===")
            print(f"作者: {feed.nickname} ({feed.uin})")
            print(f"时间: {feed.time}")
            print(f"内容: {feed.content[:100]}..." if len(feed.content) > 100 else f"内容: {feed.content}")
            print(f"点赞: {feed.likes} | 评论: {feed.comments}")
            if feed.images:
                print(f"图片: {len(feed.images)} 张")
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("publish", help="发布说说")
def publish_post(
    text: str = typer.Option(None, "--text", "-t", help="说说内容", prompt=True),
    image: Optional[str] = typer.Option(None, "--image", "-i", help="图片URL，多个用逗号分隔")
):
    try:
        async def do_publish():
            from ..utils import normalize_images
            
            images = image.split(",") if image else []
            image_bytes = None
            if images:
                image_bytes = await normalize_images(images)
            
            resp = await api.publish(text, image_bytes)
            return resp
        
        resp = asyncio.run(do_publish())
        if resp.ok:
            tid = resp.data.get("tid", "")
            typer.echo(f"发布成功！说说ID: {tid}")
        else:
            typer.echo(f"发布失败: {resp.message}", err=True)
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("like", help="点赞说说")
def like_post(
    tid: str = typer.Option(..., "--tid", help="说说ID", prompt=True),
    author_uin: int = typer.Option(..., "--author", help="作者QQ号", prompt=True)
):
    try:
        async def do_like():
            resp = await api.like(tid, author_uin)
            return resp.ok
        
        success = asyncio.run(do_like())
        if success:
            typer.echo("点赞成功！")
        else:
            typer.echo("点赞失败", err=True)
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("comment", help="评论说说")
def comment_post(
    tid: str = typer.Option(..., "--tid", help="说说ID", prompt=True),
    author_uin: int = typer.Option(..., "--author", help="作者QQ号", prompt=True),
    content: str = typer.Option(None, "--content", "-c", help="评论内容", prompt=True)
):
    try:
        async def do_comment():
            resp = await api.comment(tid, author_uin, content)
            return resp
        
        resp = asyncio.run(do_comment())
        if resp.ok:
            comment_id = resp.data.get("commentId", "")
            typer.echo(f"评论成功！评论ID: {comment_id}")
        else:
            typer.echo(f"评论失败", err=True)
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("visitors", help="获取访客记录")
def get_visitors(
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    num: int = typer.Option(20, "--num", "-n", help="每页数量")
):
    try:
        async def fetch_visitors():
            resp = await api.get_visitors(page, num)
            if resp.ok:
                return resp.data.get("visitors", [])
            return []
        
        visitors = asyncio.run(fetch_visitors())
        for i, visitor in enumerate(visitors, 1):
            print(f"\n访客 {i}: {visitor.nickname} ({visitor.uin})")
            print(f"访问时间: {visitor.time}")
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("login", help="设置Cookie登录")
def login(
    cookie: Optional[str] = typer.Option(None, "--cookie", "-c", help="Cookie字符串")
):
    if not cookie:
        cookie = typer.prompt("请输入QQ空间Cookie", hide_input=True)
    
    try:
        asyncio.run(session.login(cookie))
        typer.echo("登录成功！")
    except Exception as e:
        typer.echo(f"登录失败: {e}", err=True)


@app.command("status", help="查看登录状态")
def login_status():
    try:
        async def get_status():
            is_logged_in = session.is_logged_in
            if is_logged_in:
                ctx = await session.get_ctx()
                return is_logged_in, ctx.uin
            return is_logged_in, None
        
        is_logged_in, uin = asyncio.run(get_status())
        if is_logged_in:
            typer.echo(f"已登录 | QQ号: {uin}")
        else:
            typer.echo("未登录")
    except Exception as e:
        typer.echo(f"获取状态失败: {e}", err=True)


@app.command("generate-comment", help="AI生成评论")
def generate_comment(
    content: str = typer.Option(None, "--content", "-c", help="说说内容", prompt=True)
):
    try:
        prompt = config.llm.comment_prompt.format(content=content)
        result = asyncio.run(llm.chat("你是一个QQ空间活跃用户，擅长发表有趣的评论", prompt))
        typer.echo(f"生成的评论:\n{result}")
    except Exception as e:
        typer.echo(f"生成失败: {e}", err=True)


@app.command("generate-post", help="AI生成说说")
def generate_post(
    topic: str = typer.Option(None, "--topic", "-t", help="说说主题", prompt=True)
):
    try:
        prompt = config.llm.post_prompt.format(topic=topic)
        result = asyncio.run(llm.chat("你是一个QQ空间活跃用户，擅长发表有趣的说说", prompt))
        typer.echo(f"生成的说说:\n{result}")
    except Exception as e:
        typer.echo(f"生成失败: {e}", err=True)


def main():
    app()


if __name__ == "__main__":
    main()