import json
import typer
from typing import Optional, Any
from pathlib import Path

from ...config_manager import default_manager, ConfigSchema
from ..utils import format_config_value, validate_port

app = typer.Typer(
    name="config",
    help="配置管理命令",
    no_args_is_help=True,
    rich_markup_mode="rich"
)


def register_config_commands(main_app: typer.Typer) -> None:
    """
    注册配置管理相关命令
    """
    main_app.add_typer(app, name="config")


@app.command("get", help="查询配置项")
def get_config(
    key: str = typer.Argument(..., help="配置键，如 qzone.cookie"),
    show_sensitive: bool = typer.Option(False, "--show-sensitive", "-s", 
        help="显示敏感信息（默认脱敏显示）")
):
    """
    查询指定配置项的值
    
    示例:
      qzone-cli config get qzone.timeout
      qzone-cli config get onebot.enabled
      qzone-cli config get qzone.cookie -s  # 显示完整cookie
    """
    manager = default_manager
    config = manager.load()
    
    value = manager.get(key)
    if value is None:
        typer.echo(f"[red]配置项 '{key}' 不存在[/red]")
        raise typer.Exit(code=1)
    
    # 检查是否为敏感字段
    is_sensitive = key in ConfigSchema.SENSITIVE_FIELDS
    
    if is_sensitive and not show_sensitive:
        typer.echo(f"{key} = [yellow]****** (使用 -s 参数查看完整值)[/yellow]")
    else:
        typer.echo(f"{key} = {format_config_value(value)}")


@app.command("set", help="设置配置项")
def set_config(
    key: str = typer.Argument(..., help="配置键，如 qzone.timeout"),
    value: str = typer.Argument(..., help="配置值")
):
    """
    设置指定配置项的值
    
    示例:
      qzone-cli config set qzone.timeout 60
      qzone-cli config set onebot.enabled true
      qzone-cli config set log.level DEBUG
    """
    manager = default_manager
    
    # 验证特殊配置项
    if key == "onebot.port":
        try:
            port = int(value)
            validate_port(port)
        except ValueError as e:
            typer.echo(f"[red]端口号无效: {e}[/red]")
            raise typer.Exit(code=1)
    
    if key == "onebot.enabled":
        value = value.lower() == "true"
    
    if key in ["qzone.timeout", "qzone.max_retries", "qzone.retry_delay", 
               "onebot.timeout", "log.max_size", "log.backup_count"]:
        try:
            value = int(value)
        except ValueError:
            typer.echo(f"[red]'{key}' 必须为整数[/red]")
            raise typer.Exit(code=1)
    
    if key == "log.level":
        valid_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
        if value.upper() not in valid_levels:
            typer.echo(f"[red]日志级别必须为: {', '.join(valid_levels)}[/red]")
            raise typer.Exit(code=1)
        value = value.upper()
    
    try:
        manager.set(key, value)
        typer.echo(f"[green]配置 '{key}' 已更新为: {format_config_value(value)}[/green]")
    except Exception as e:
        typer.echo(f"[red]更新配置失败: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("reset", help="重置配置项")
def reset_config(
    key: Optional[str] = typer.Argument(None, help="配置键，如 qzone.timeout，不指定则重置所有")
):
    """
    重置配置项为默认值
    
    示例:
      qzone-cli config reset qzone.timeout
      qzone-cli config reset onebot
      qzone-cli config reset  # 重置所有配置
    """
    manager = default_manager
    
    if key is None:
        confirm = typer.confirm("确定要重置所有配置吗？此操作不可撤销！")
        if not confirm:
            typer.echo("[yellow]操作已取消[/yellow]")
            raise typer.Exit(code=0)
    
    try:
        manager.reset(key)
        if key:
            typer.echo(f"[green]配置 '{key}' 已重置为默认值[/green]")
        else:
            typer.echo("[green]所有配置已重置为默认值[/green]")
    except Exception as e:
        typer.echo(f"[red]重置配置失败: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("list", help="列出所有配置项")
def list_config(
    show_sensitive: bool = typer.Option(False, "--show-sensitive", "-s", 
        help="显示敏感信息（默认脱敏显示）")
):
    """
    列出所有配置项及其值
    
    示例:
      qzone-cli config list
      qzone-cli config list -s  # 显示敏感信息
    """
    manager = default_manager
    config = manager.load()
    
    typer.echo("\n[bold blue]QQ空间MCP 配置列表[/bold blue]")
    typer.echo("-" * 60)
    
    def print_section(name: str, section: Any, prefix: str = ""):
        if hasattr(section, "__dict__") or isinstance(section, dict):
            items = section.__dict__ if hasattr(section, "__dict__") else section
            for key, value in items.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if hasattr(value, "__dict__") or isinstance(value, dict):
                    typer.echo(f"\n[bold]{key}:[/bold]")
                    print_section(key, value, full_key)
                else:
                    is_sensitive = full_key in ConfigSchema.SENSITIVE_FIELDS
                    if is_sensitive and not show_sensitive:
                        typer.echo(f"  {key} = [yellow]******[/yellow]")
                    else:
                        typer.echo(f"  {key} = {format_config_value(value)}")
    
    print_section("", config)
    typer.echo("\n")


@app.command("onboard", help="交互式配置向导")
def onboard():
    """
    交互式配置向导，引导用户完成初始配置
    
    示例:
      qzone-cli config onboard
    """
    typer.echo("\n[bold blue]🚀 QQ空间MCP 配置向导[/bold blue]")
    typer.echo("=" * 60)
    typer.echo("此向导将引导您完成基本配置设置")
    typer.echo("=" * 60 + "\n")
    
    manager = default_manager
    config = manager.load()
    
    # 配置QQ空间相关
    typer.echo("[bold green]📦 第1步：QQ空间配置[/bold green]")
    typer.echo("-" * 40)
    
    cookie = typer.prompt("请输入QQ空间Cookie（留空跳过）", default="", hide_input=True)
    if cookie:
        config.qzone.cookie = cookie
    
    timeout = typer.prompt("请求超时时间(秒)", default=str(config.qzone.timeout))
    try:
        config.qzone.timeout = int(timeout)
    except ValueError:
        typer.echo(f"[yellow]无效的超时时间，使用默认值: {config.qzone.timeout}[/yellow]")
    
    max_retries = typer.prompt("最大重试次数", default=str(config.qzone.max_retries))
    try:
        config.qzone.max_retries = int(max_retries)
    except ValueError:
        typer.echo(f"[yellow]无效的重试次数，使用默认值: {config.qzone.max_retries}[/yellow]")
    
    # 配置OneBot
    typer.echo("\n[bold green]📦 第2步：OneBot配置（可选）[/bold green]")
    typer.echo("-" * 40)
    
    enabled = typer.confirm("是否启用OneBot自动获取Cookie?", default=config.onebot.enabled)
    config.onebot.enabled = enabled
    
    if enabled:
        provider = typer.prompt("OneBot客户端类型", 
                               default=config.onebot.provider,
                               show_default=True)
        config.onebot.provider = provider
        
        host = typer.prompt("OneBot服务地址", 
                           default=config.onebot.host,
                           show_default=True)
        config.onebot.host = host
        
        while True:
            port = typer.prompt("OneBot端口", 
                               default=str(config.onebot.port),
                               show_default=True)
            try:
                port_int = int(port)
                validate_port(port_int)
                config.onebot.port = port_int
                break
            except ValueError as e:
                typer.echo(f"[red]错误: {e}，请重新输入[/red]")
        
        timeout = typer.prompt("请求超时时间(秒)", 
                              default=str(config.onebot.timeout),
                              show_default=True)
        try:
            config.onebot.timeout = int(timeout)
        except ValueError:
            typer.echo(f"[yellow]无效的超时时间，使用默认值: {config.onebot.timeout}[/yellow]")
        
        api_path = typer.prompt("获取Cookie的API路径", 
                               default=config.onebot.api_path,
                               show_default=True)
        config.onebot.api_path = api_path
        
        token = typer.prompt("Bearer Token（留空跳过）", 
                            default="", 
                            hide_input=True)
        config.onebot.token = token
    
    # 配置日志
    typer.echo("\n[bold green]📦 第3步：日志配置[/bold green]")
    typer.echo("-" * 40)
    
    log_level = typer.prompt("日志级别", 
                            default=config.log.level,
                            show_default=True)
    valid_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
    if log_level.upper() in valid_levels:
        config.log.level = log_level.upper()
    else:
        typer.echo(f"[yellow]无效的日志级别，使用默认值: {config.log.level}[/yellow]")
    
    console_enabled = typer.confirm("是否输出到控制台?", default=config.log.console_enabled)
    config.log.console_enabled = console_enabled
    
    file_enabled = typer.confirm("是否输出到文件?", default=config.log.file_enabled)
    config.log.file_enabled = file_enabled
    
    # 配置预览
    typer.echo("\n" + "=" * 60)
    typer.echo("[bold blue]📋 配置预览[/bold blue]")
    typer.echo("=" * 60)
    
    typer.echo("\n[bold]QQ空间配置:[/bold]")
    typer.echo(f"  Cookie: {'已设置' if config.qzone.cookie else '未设置'}")
    typer.echo(f"  超时时间: {config.qzone.timeout}秒")
    typer.echo(f"  最大重试: {config.qzone.max_retries}次")
    
    typer.echo("\n[bold]OneBot配置:[/bold]")
    typer.echo(f"  启用: {'是' if config.onebot.enabled else '否'}")
    if config.onebot.enabled:
        typer.echo(f"  类型: {config.onebot.provider}")
        typer.echo(f"  地址: {config.onebot.host}:{config.onebot.port}")
        typer.echo(f"  API路径: {config.onebot.api_path}")
        typer.echo(f"  Token: {'已设置' if config.onebot.token else '未设置'}")
    
    typer.echo("\n[bold]日志配置:[/bold]")
    typer.echo(f"  级别: {config.log.level}")
    typer.echo(f"  控制台输出: {'是' if config.log.console_enabled else '否'}")
    typer.echo(f"  文件输出: {'是' if config.log.file_enabled else '否'}")
    
    typer.echo("\n" + "=" * 60)
    confirm = typer.confirm("确认保存以上配置?", default=True)
    
    if confirm:
        try:
            manager.save(config)
            typer.echo("\n[green]✅ 配置已成功保存！[/green]")
            typer.echo(f"配置文件路径: {manager.config_path}")
        except Exception as e:
            typer.echo(f"\n[red]❌ 保存配置失败: {e}[/red]")
            raise typer.Exit(code=1)
    else:
        typer.echo("\n[yellow]配置已取消，未保存任何更改[/yellow]")


@app.command("export", help="导出配置到文件")
def export_config(
    output_path: Path = typer.Argument(..., help="导出文件路径")
):
    """
    导出当前配置到指定文件
    
    示例:
      qzone-cli config export /path/to/config.json
    """
    manager = default_manager
    
    try:
        manager.export(output_path)
        typer.echo(f"[green]配置已导出到: {output_path}[/green]")
    except Exception as e:
        typer.echo(f"[red]导出配置失败: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("import", help="从文件导入配置")
def import_config(
    input_path: Path = typer.Argument(..., help="导入文件路径")
):
    """
    从指定文件导入配置
    
    示例:
      qzone-cli config import /path/to/config.json
    """
    manager = default_manager
    
    if not input_path.exists():
        typer.echo(f"[red]文件不存在: {input_path}[/red]")
        raise typer.Exit(code=1)
    
    try:
        manager.import_config(input_path)
        typer.echo(f"[green]配置已从 {input_path} 导入[/green]")
    except Exception as e:
        typer.echo(f"[red]导入配置失败: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("path", help="显示配置文件路径")
def show_config_path():
    """
    显示当前配置文件的路径
    
    示例:
      qzone-cli config path
    """
    manager = default_manager
    typer.echo(f"配置文件路径: {manager.config_path}")
    typer.echo(f"数据目录: {manager.data_dir}")