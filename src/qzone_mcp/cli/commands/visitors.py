import typer
from typing import Optional

from ..app import get_api, async_command
from ..errors import async_handle_cli_error


def register_visitors_commands(app: typer.Typer) -> None:
    """
    注册访客相关命令
    """
    @app.command("visitors", help="获取访客记录")
    @async_command
    @async_handle_cli_error
    async def get_visitors(
        page: int = typer.Option(1, "--page", "-p", 
            help="页码，从1开始", min=1),
        num: int = typer.Option(20, "--num", "-n", 
            help="每页数量，范围1-100", min=1, max=100)
    ):
        """
        获取QQ空间访客记录
        
        示例:
          qzone-cli visitors                    # 获取第1页访客（20条）
          qzone-cli visitors -p 2               # 获取第2页访客
          qzone-cli visitors -n 10              # 每页10条
          qzone-cli visitors -p 3 -n 15         # 获取第3页，每页15条
        """
        api = get_api()
        
        resp = await api.get_visitors(page, num)
        
        if not resp.ok:
            typer.echo(f"[red]获取失败[/red]: {resp.message}", err=True)
            raise typer.Exit(code=1)
        
        visitors = resp.data.get("visitors", [])
        
        if not visitors:
            typer.echo("[yellow]暂无访客记录[/yellow]")
            return
        
        typer.echo(f"\n[bold]=== 访客记录 第 {page} 页 ===")
        for i, visitor in enumerate(visitors, 1):
            typer.echo(f"\n访客 {i}:")
            typer.echo(f"  昵称: {visitor.nickname}")
            typer.echo(f"  QQ号: {visitor.uin}")
            typer.echo(f"  访问时间: {visitor.time}")
