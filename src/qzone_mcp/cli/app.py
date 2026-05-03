import asyncio
import typer
from typing import Optional, Any, Coroutine, Callable
from functools import wraps

from ..config import config
from ..session import QzoneSession
from ..api.client import QzoneHttpClient
from ..api.qzone_api import QzoneAPI
from .commands import register_all_commands

app = typer.Typer(
    name="qzone-cli",
    help="QQ空间命令行工具",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich"
)

session = QzoneSession(config)
http_client = QzoneHttpClient(session, config)
api = QzoneAPI(http_client)


def get_session() -> QzoneSession:
    return session


def get_api() -> QzoneAPI:
    return api


def get_config():
    return config


def async_command(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Any]:
    """
    装饰器：将异步函数转换为同步命令
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        async def run_and_cleanup():
            try:
                return await func(*args, **kwargs)
            finally:
                await http_client.close()
        
        return asyncio.run(run_and_cleanup())
    return wrapper


register_all_commands(app)


def main():
    app()


if __name__ == "__main__":
    main()
