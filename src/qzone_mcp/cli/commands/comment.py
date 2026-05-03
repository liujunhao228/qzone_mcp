import typer
from typing import Optional

from ..app import get_api, async_command
from ..errors import async_handle_cli_error


def register_comment_commands(app: typer.Typer) -> None:
    """
    注册评论相关命令
    """
    @app.command("comment", help="评论说说")
    @async_command
    @async_handle_cli_error
    async def comment_post(
        tid: str = typer.Option(..., "--tid", 
            help="说说ID", prompt="请输入说说ID"),
        author_uin: int = typer.Option(..., "--author", 
            help="作者QQ号", prompt="请输入作者QQ号"),
        content: str = typer.Option(None, "--content", "-c", 
            help="评论内容", prompt="请输入评论内容")
    ):
        """
        评论指定说说
        
        示例:
          qzone-cli comment --tid 123456789 --author 987654321 -c "支持！"
        """
        api = get_api()
        
        if not content.strip():
            raise ValueError("评论内容不能为空")
        
        resp = await api.comment(tid, author_uin, content.strip())
        
        if resp.ok:
            comment_id = resp.data.get("commentId", "")
            typer.echo(f"[green]评论成功！[/green]评论ID: {comment_id}")
        else:
            typer.echo(f"[red]评论失败[/red]: {resp.message}", err=True)
            raise typer.Exit(code=1)
