"""日志上下文管理模块"""
import uuid
from contextvars import ContextVar

_request_id_ctx: ContextVar[str] = ContextVar('request_id', default='N/A')


def set_request_id(request_id: str | None = None) -> str:
    """设置当前请求ID，用于日志追踪"""
    if request_id is None:
        request_id = f"req-{uuid.uuid4().hex[:8]}"
    _request_id_ctx.set(request_id)
    return request_id


def get_request_id() -> str:
    """获取当前请求ID"""
    return _request_id_ctx.get()