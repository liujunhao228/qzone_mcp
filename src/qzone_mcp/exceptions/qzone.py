from typing import Optional


class QzoneError(Exception):
    """Qzone 基础异常"""
    code: int = 0
    message: str = "Qzone API 错误"
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.message)
        self.message = message or self.message


class LoginExpiredError(QzoneError):
    """登录失效异常"""
    code = -3000
    message = "登录已失效，请重新登录"


class PermissionDeniedError(QzoneError):
    """权限不足异常"""
    code = 403
    message = "权限不足，无法访问该资源"


class ApiRateLimitError(QzoneError):
    """API 限流异常"""
    code = 429
    message = "请求过于频繁，请稍后重试"


class NetworkError(QzoneError):
    """网络错误异常"""
    code = -1
    message = "网络请求失败"


class ParseError(QzoneError):
    """解析错误异常"""
    code = -2
    message = "响应解析失败"
