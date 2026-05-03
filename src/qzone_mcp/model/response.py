from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .constants import QZONE_CODE_OK, QZONE_CODE_UNKNOWN, QZONE_INTERNAL_META_KEY


class ApiResponse(BaseModel):
    ok: bool = Field(description="操作是否成功")
    code: int = Field(description="业务状态码")
    message: Optional[str] = Field(default=None, description="错误信息")
    data: Dict[str, Any] = Field(default_factory=dict, description="业务数据")
    raw: Dict[str, Any] = Field(default_factory=dict, description="原始响应")

    @classmethod
    def from_raw(
        cls,
        raw: Dict[str, Any],
        *,
        code_key: str = "code",
        msg_key: str | tuple[str, ...] = ("message", "msg"),
        data_key: str | None = None,
        success_code: int = QZONE_CODE_OK,
    ) -> "ApiResponse":
        code = raw.get(code_key, QZONE_CODE_UNKNOWN)

        message = None
        if isinstance(msg_key, tuple):
            for k in msg_key:
                if raw.get(k):
                    message = raw.get(k)
                    break
        else:
            message = raw.get(msg_key) or raw.get("data", {}).get(msg_key) or code

        if code == success_code:
            if data_key is None:
                data = dict(raw)
                data.pop(QZONE_INTERNAL_META_KEY, None)
            else:
                data = raw.get(data_key, {})
            return cls(
                ok=True,
                code=code,
                message=None,
                data=data,
                raw=raw,
            )

        return cls(
            ok=False,
            code=code,
            message=str(message) if message else None,
            data={},
            raw=raw,
        )

    def __bool__(self) -> bool:
        return self.ok

    def unwrap(self) -> Dict[str, Any]:
        if not self.ok:
            raise RuntimeError(f"API Error {self.code}: {self.message}")
        return self.data

    def get(self, key: str, default: Any = None) -> Any:
        if not self.ok or not self.data:
            return default
        return self.data.get(key, default)

    def __repr__(self) -> str:
        if self.ok:
            return f"<ApiResponse ok code={self.code}>"
        return f"<ApiResponse fail code={self.code} message={self.message!r}>"
