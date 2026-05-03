import typer
from typing import Optional

from ..app import get_api, get_config, async_command
from ..errors import async_handle_cli_error

draft_app = typer.Typer(name="draft", help="草稿管理")


def register_draft_commands(app: typer.Typer) -> None:
    """
    注册草稿相关命令
    """
    app.add_typer(draft_app, name="draft")


@draft_app.command("list", help="列出草稿")
@async_command
@async_handle_cli_error
async def list_drafts(
    page: int = typer.Option(1, "--page", "-p", 
        help="页码，从1开始", min=1),
    num: int = typer.Option(20, "--num", "-n", 
        help="每页数量，范围1-100", min=1, max=100)
):
    """
    列出保存的草稿列表
    
    示例:
      qzone-cli draft list              # 列出第1页草稿（20条）
      qzone-cli draft list -p 2         # 列出第2页草稿
      qzone-cli draft list -n 10        # 每页10条
    """
    from ...draft import DraftService
    
    cfg = get_config()
    draft_service = DraftService(cfg)
    offset = (page - 1) * num
    drafts = await draft_service.get_drafts(limit=num, offset=offset)
    
    if not drafts:
        typer.echo("[yellow]暂无草稿[/yellow]")
        return
    
    typer.echo(f"\n[bold]=== 草稿列表 第 {page} 页 ===")
    for draft in drafts:
        typer.echo(f"\n草稿ID: {draft.get('id', '')}")
        content = draft.get("content", "")
        typer.echo(f"  内容预览: {content[:50]}..." if len(content) > 50 else f"  内容: {content}")
        images = draft.get("images", [])
        typer.echo(f"  图片数量: {len(images) if images else 0}")
        typer.echo(f"  创建时间: {draft.get('created_at', '')}")
        typer.echo(f"  更新时间: {draft.get('updated_at', '')}")


@draft_app.command("save", help="保存草稿")
@async_command
@async_handle_cli_error
async def save_draft(
    text: str = typer.Option(None, "--text", "-t", 
        help="草稿内容", prompt=True),
    image: Optional[str] = typer.Option(None, "--image", "-i", 
        help="图片URL，多个用逗号分隔"),
    draft_id: Optional[int] = typer.Option(None, "--id", 
        help="草稿ID（更新现有草稿时使用）")
):
    """
    保存说说草稿
    
    示例:
      qzone-cli draft save -t "今天天气真好"           # 保存新草稿
      qzone-cli draft save -t "修改后的内容" --id 1    # 更新指定草稿
      qzone-cli draft save -t "带图片" -i "https://example.com/img.jpg"  # 带图片
    """
    from ...draft import DraftService
    
    if not text.strip():
        raise ValueError("草稿内容不能为空")
    
    cfg = get_config()
    draft_service = DraftService(cfg)
    
    images = image.split(",") if image else []
    
    if draft_id:
        result = await draft_service.update_draft(draft_id, text.strip(), None, images)
        if result:
            typer.echo(f"[green]草稿更新成功！[/green]草稿ID: {draft_id}")
        else:
            typer.echo(f"[red]草稿更新失败[/red]，草稿ID不存在", err=True)
            raise typer.Exit(code=1)
    else:
        draft = await draft_service.create_draft(text.strip(), None, images)
        typer.echo(f"[green]草稿保存成功！[/green]草稿ID: {draft.get('id', '')}")


@draft_app.command("delete", help="删除草稿")
@async_command
@async_handle_cli_error
async def delete_draft(
    draft_id: int = typer.Option(..., "--id", 
        help="草稿ID", prompt="请输入草稿ID")
):
    """
    删除指定草稿
    
    示例:
      qzone-cli draft delete --id 1
    """
    from ...draft import DraftService
    
    cfg = get_config()
    draft_service = DraftService(cfg)
    
    success = await draft_service.delete_draft(draft_id)
    
    if success:
        typer.echo(f"[green]草稿删除成功！[/green]")
    else:
        typer.echo(f"[red]草稿删除失败[/red]，草稿ID不存在", err=True)
        raise typer.Exit(code=1)


@draft_app.command("publish", help="发布草稿")
@async_command
@async_handle_cli_error
async def publish_draft(
    draft_id: int = typer.Option(..., "--id", 
        help="草稿ID", prompt="请输入草稿ID")
):
    """
    发布指定草稿
    
    示例:
      qzone-cli draft publish --id 1
    """
    from ...draft import DraftService
    
    cfg = get_config()
    draft_service = DraftService(cfg)
    api = get_api()
    
    draft = await draft_service.get_draft(draft_id)
    
    if not draft:
        typer.echo(f"[red]草稿不存在[/red]，草稿ID: {draft_id}", err=True)
        raise typer.Exit(code=1)
    
    image_bytes = None
    images = draft.get("images", [])
    if images:
        from ...utils import normalize_images
        image_bytes = await normalize_images(images)
    
    resp = await api.publish(draft.get("content", ""), image_bytes)
    
    if resp.ok:
        tid = resp.data.get("tid", "")
        typer.echo(f"[green]发布成功！[/green]说说ID: {tid}")
        
        await draft_service.delete_draft(draft_id)
        typer.echo(f"[green]草稿已自动删除[/green]")
    else:
        typer.echo(f"[red]发布失败[/red]: {resp.message}", err=True)
        raise typer.Exit(code=1)
