import typer
from typing import Optional

from ..app import get_api, async_command
from ..errors import async_handle_cli_error
from ..utils import truncate_text
from ...model import Feed


def register_feeds_commands(app: typer.Typer) -> None:
    """
    注册说说相关命令
    """
    @app.command("feeds", help="获取说说列表")
    @async_command
    @async_handle_cli_error
    async def get_feeds(
        user: Optional[str] = typer.Option(None, "--user", "-u", 
            help="目标QQ号，默认为当前登录用户"),
        num: int = typer.Option(5, "--num", "-n", 
            help="获取数量，范围1-100", min=1, max=100),
        detail: bool = typer.Option(False, "--detail", "-d", 
            help="获取详细信息")
    ):
        """
        获取QQ空间说说列表
        
        示例:
          qzone-cli feeds                    # 获取当前用户5条说说
          qzone-cli feeds -u 123456789       # 获取指定用户5条说说
          qzone-cli feeds -n 20              # 获取20条说说
          qzone-cli feeds -u 123456789 -n 10 -d  # 获取指定用户10条详细说说
        """
        api = get_api()
        
        resp = await api.get_feeds(user or "", pos=0, num=num, with_detail=detail)
        if not resp.ok:
            typer.echo(f"[red]获取失败[/red]: {resp.message}", err=True)
            raise typer.Exit(code=1)
        
        feeds_data = resp.data.get("feeds", [])
        feeds = [Feed(**feed) for feed in feeds_data]
        
        if not feeds:
            typer.echo("[yellow]暂无说说[/yellow]")
            return
        
        for i, feed in enumerate(feeds, 1):
            typer.echo(f"\n[bold]=== 说说 {i} ===")
            typer.echo(f"作者: {feed.nickname} ({feed.uin})")
            typer.echo(f"时间: {feed.time}")
            typer.echo(f"内容: {truncate_text(feed.content)}")
            typer.echo(f"点赞: {feed.likes} | 评论: {feed.comments}")
            if feed.images:
                typer.echo(f"图片: {len(feed.images)} 张")
            if feed.tid:
                typer.echo(f"说说ID: {feed.tid}")
    
    @app.command("publish", help="发布说说")
    @async_command
    @async_handle_cli_error
    async def publish_post(
        text: str = typer.Option(None, "--text", "-t", 
            help="说说内容", prompt=True),
        image: Optional[str] = typer.Option(None, "--image", "-i", 
            help="图片URL，多个用逗号分隔")
    ):
        """
        发布QQ空间说说
        
        示例:
          qzone-cli publish -t "今天天气真好"           # 发布纯文字说说
          qzone-cli publish -t "风景不错" -i "https://example.com/img.jpg"  # 带图片
          qzone-cli publish -t "多图测试" -i "url1,url2,url3"  # 多张图片
        """
        api = get_api()
        
        if not text.strip():
            raise ValueError("说说内容不能为空")
        
        images = image.split(",") if image else []
        image_bytes = None
        
        if images:
            from ...utils import normalize_images
            image_bytes = await normalize_images(images)
        
        resp = await api.publish(text.strip(), image_bytes)
        
        if resp.ok:
            tid = resp.data.get("tid", "")
            typer.echo(f"[green]发布成功！[/green]说说ID: {tid}")
        else:
            typer.echo(f"[red]发布失败[/red]: {resp.message}", err=True)
            raise typer.Exit(code=1)
    
    @app.command("like", help="点赞说说")
    @async_command
    @async_handle_cli_error
    async def like_post(
        tid: str = typer.Option(..., "--tid", 
            help="说说ID", prompt="请输入说说ID"),
        author_uin: int = typer.Option(..., "--author", 
            help="作者QQ号", prompt="请输入作者QQ号")
    ):
        """
        点赞指定说说
        
        示例:
          qzone-cli like --tid 123456789 --author 987654321
        """
        api = get_api()
        
        resp = await api.like(tid, author_uin)
        
        if resp.ok:
            typer.echo("[green]点赞成功！[/green]")
        else:
            typer.echo(f"[red]点赞失败[/red]: {resp.message}", err=True)
            raise typer.Exit(code=1)

    @app.command("detail", help="查看说说详情")
    @async_command
    @async_handle_cli_error
    async def get_post_detail(
        tid: str = typer.Option(..., "--tid", 
            help="说说ID", prompt="请输入说说ID"),
        author_uin: int = typer.Option(..., "--author", 
            help="作者QQ号", prompt="请输入作者QQ号")
    ):
        """
        获取指定说说的完整详情，包括点赞数、评论数、转发数、浏览数和完整评论列表
        
        示例:
          qzone-cli detail --tid 123456789 --author 987654321
        """
        api = get_api()
        
        resp = await api.get_post_detail(tid, author_uin)
        
        if not resp.ok:
            typer.echo(f"[red]获取失败[/red]: {resp.message}", err=True)
            raise typer.Exit(code=1)
        
        feed_data = resp.data.get("feed")
        if not feed_data:
            typer.echo("[yellow]未找到说说详情[/yellow]")
            return
        
        feed = Feed(**feed_data)
        
        typer.echo("\n" + "="*50)
        typer.echo("[bold]📝 说说详情[/bold]")
        typer.echo("="*50)
        typer.echo(f"👤 作者: {feed.nickname or '未知'} ({feed.uin})")
        typer.echo(f"🕐 时间: {feed.time or '未知'}")
        if feed.source_name:
            typer.echo(f"📱 来源: {feed.source_name}")
        typer.echo("")
        
        typer.echo("📄 内容:")
        typer.echo(f"  {feed.content or '(空内容)'}")
        typer.echo("")
        
        if feed.rt_con:
            typer.echo("🔄 转发内容:")
            typer.echo(f"  {feed.rt_con}")
            typer.echo("")
        
        typer.echo("📊 统计信息:")
        typer.echo(f"  ❤️  点赞: {feed.likes}")
        typer.echo(f"  💬 评论: {feed.comments}")
        typer.echo(f"  🔄 转发: {feed.shares}")
        typer.echo(f"  👁️  浏览: {feed.views}")
        typer.echo("")
        
        if feed.images:
            typer.echo(f"🖼️  图片: {len(feed.images)} 张")
        if feed.videos:
            typer.echo(f"🎥  视频: {len(feed.videos)} 个")
        typer.echo("")
        
        typer.echo("💬 评论列表:")
        if feed.comment_list:
            # 按层级组织评论
            main_comments = [c for c in feed.comment_list if c.parent_id is None]
            
            for i, comment in enumerate(main_comments, 1):
                typer.echo(f"\n  {i}. {comment.nickname or '匿名'}({comment.uin}):")
                typer.echo(f"     {comment.content}")
                typer.echo(f"     🕐 {comment.time or '未知'}")
                
                # 楼中楼回复
                replies = [c for c in feed.comment_list if c.parent_id == comment.id]
                for j, reply in enumerate(replies, 1):
                    typer.echo(f"       ↩️  {j}. {reply.nickname or '匿名'}: {reply.content}")
        else:
            typer.echo("  暂无评论")
        
        typer.echo("\n" + "="*50)
        typer.echo(f"🔗 链接: https://user.qzone.qq.com/{feed.uin}/mood/{feed.tid}")
