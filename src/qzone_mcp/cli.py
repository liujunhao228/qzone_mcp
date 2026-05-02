import asyncio
import json
from typing import Optional, List

import typer

from .api.session import QzoneSession
from .api.client import QzoneClient
from .adapters.llm import create_llm_adapter
from .config import config

app = typer.Typer(name="qzone-cli", help="QQ空间命令行工具")

session = QzoneSession(config)
client = QzoneClient(session)
llm = create_llm_adapter(config)


@app.command("feeds", help="获取说说列表")
def get_feeds(
    user: Optional[str] = typer.Option(None, "--user", "-u", help="目标QQ号"),
    num: int = typer.Option(5, "--num", "-n", help="获取数量"),
    detail: bool = typer.Option(False, "--detail", "-d", help="获取详情")
):
    try:
        feeds = asyncio.run(client.get_feeds(user, 0, num, detail))
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
        images = image.split(",") if image else []
        result = asyncio.run(client.publish_post(text, images))
        if result.success:
            typer.echo(f"发布成功！说说ID: {result.tid}")
        else:
            typer.echo(f"发布失败: {result.message}", err=True)
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("like", help="点赞说说")
def like_post(
    tid: str = typer.Option(..., "--tid", help="说说ID", prompt=True),
    author_uin: int = typer.Option(..., "--author", help="作者QQ号", prompt=True)
):
    try:
        result = asyncio.run(client.like_post(tid, author_uin))
        if result.success:
            typer.echo("点赞成功！")
        else:
            typer.echo(f"点赞失败: {result.message}", err=True)
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("comment", help="评论说说")
def comment_post(
    tid: str = typer.Option(..., "--tid", help="说说ID", prompt=True),
    author_uin: int = typer.Option(..., "--author", help="作者QQ号", prompt=True),
    content: str = typer.Option(None, "--content", "-c", help="评论内容", prompt=True)
):
    try:
        result = asyncio.run(client.comment_post(tid, author_uin, content))
        if result.success:
            typer.echo(f"评论成功！评论ID: {result.comment_id}")
        else:
            typer.echo(f"评论失败: {result.message}", err=True)
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)


@app.command("visitors", help="获取访客记录")
def get_visitors(
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    num: int = typer.Option(20, "--num", "-n", help="每页数量")
):
    try:
        visitors = asyncio.run(client.get_visitors(page, num))
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
        is_logged_in = session.is_logged_in
        if is_logged_in:
            ctx = asyncio.run(session.get_ctx())
            typer.echo(f"已登录 | QQ号: {ctx.uin}")
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