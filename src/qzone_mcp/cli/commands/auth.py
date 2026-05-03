import typer
from typing import Optional

from ..app import get_session, async_command
from ..errors import async_handle_cli_error


def register_auth_commands(app: typer.Typer) -> None:
    """
    注册认证相关命令
    """
    @app.command("login", help="设置Cookie登录")
    @async_command
    @async_handle_cli_error
    async def login(
        cookie: Optional[str] = typer.Option(None, "--cookie", "-c", 
            help="Cookie字符串，若不提供将交互式输入")
    ):
        """
        设置Cookie登录QQ空间
        
        示例:
          qzone-cli login                                # 交互式输入Cookie
          qzone-cli login -c "uin=xxx; skey=xxx; p_skey=xxx"  # 直接传入Cookie
        """
        session = get_session()
        
        if not cookie:
            cookie = typer.prompt("请输入QQ空间Cookie", hide_input=True)
        
        if not cookie.strip():
            raise ValueError("Cookie不能为空")
        
        await session.login(cookie)
        typer.echo("[green]登录成功！[/green]")
    
    @app.command("status", help="查看登录状态")
    @async_command
    @async_handle_cli_error
    async def login_status():
        """
        查看当前登录状态
        
        示例:
          qzone-cli status
        """
        session = get_session()
        is_logged_in = session.is_logged_in
        
        if is_logged_in:
            ctx = await session.get_ctx()
            typer.echo(f"[green]已登录[/green] | QQ号: {ctx.uin}")
        else:
            typer.echo("[yellow]未登录[/yellow]")
    
    @app.command("logout", help="登出当前账号")
    @async_command
    @async_handle_cli_error
    async def logout():
        """
        登出当前账号，清除会话信息
        
        示例:
          qzone-cli logout
        """
        session = get_session()
        await session.invalidate()
        typer.echo("[green]已登出[/green]")
