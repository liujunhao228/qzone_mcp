import asyncio
import typer
from functools import wraps
from typing import Callable, Any, TypeVar, Coroutine

from ..exceptions import (
    QzoneError,
    LoginExpiredError,
    PermissionDeniedError,
    ApiRateLimitError,
    NetworkError,
    ParseError,
)

F = TypeVar("F", bound=Callable[..., Any])


def handle_cli_error(func: F) -> F:
    """
    统一的CLI错误处理装饰器
    
    捕获并处理各种异常，提供友好的错误提示
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except typer.Exit:
            raise
        except LoginExpiredError as e:
            typer.echo(f"[red]认证失败[/red]: {e}\n请使用 `qzone-cli login` 重新登录", err=True)
            raise typer.Exit(code=2)
        except PermissionDeniedError as e:
            typer.echo(f"[red]权限不足[/red]: {e}", err=True)
            raise typer.Exit(code=3)
        except ApiRateLimitError as e:
            typer.echo(f"[yellow]请求受限[/yellow]: {e}", err=True)
            raise typer.Exit(code=4)
        except NetworkError as e:
            typer.echo(f"[red]网络错误[/red]: {e}", err=True)
            raise typer.Exit(code=5)
        except ParseError as e:
            typer.echo(f"[red]解析错误[/red]: {e}", err=True)
            raise typer.Exit(code=6)
        except QzoneError as e:
            typer.echo(f"[red]QQ空间错误[/red]: {e}", err=True)
            raise typer.Exit(code=7)
        except ValueError as e:
            typer.echo(f"[red]参数错误[/red]: {e}", err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"[red]未知错误[/red]: {e}", err=True)
            raise typer.Exit(code=255)
    
    return wrapper  # type: ignore


def async_handle_cli_error(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    异步函数的CLI错误处理装饰器
    
    注意：此装饰器返回的仍然是协程，需要在已有事件循环中调用
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except typer.Exit:
            raise
        except LoginExpiredError as e:
            typer.echo(f"[red]认证失败[/red]: {e}\n请使用 `qzone-cli login` 重新登录", err=True)
            raise typer.Exit(code=2)
        except PermissionDeniedError as e:
            typer.echo(f"[red]权限不足[/red]: {e}", err=True)
            raise typer.Exit(code=3)
        except ApiRateLimitError as e:
            typer.echo(f"[yellow]请求受限[/yellow]: {e}", err=True)
            raise typer.Exit(code=4)
        except NetworkError as e:
            typer.echo(f"[red]网络错误[/red]: {e}", err=True)
            raise typer.Exit(code=5)
        except ParseError as e:
            typer.echo(f"[red]解析错误[/red]: {e}", err=True)
            raise typer.Exit(code=6)
        except QzoneError as e:
            typer.echo(f"[red]QQ空间错误[/red]: {e}", err=True)
            raise typer.Exit(code=7)
        except ValueError as e:
            typer.echo(f"[red]参数错误[/red]: {e}", err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"[red]未知错误[/red]: {e}", err=True)
            raise typer.Exit(code=255)
    
    return wrapper
