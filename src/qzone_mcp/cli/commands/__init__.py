from typing import Any


def register_all_commands(app: Any) -> None:
    """
    注册所有命令到应用
    
    采用延迟导入方式，避免循环依赖和启动性能问题
    """
    from .auth import register_auth_commands
    from .feeds import register_feeds_commands
    from .comment import register_comment_commands
    from .visitors import register_visitors_commands
    from .draft import register_draft_commands
    from .config import register_config_commands
    
    register_auth_commands(app)
    register_feeds_commands(app)
    register_comment_commands(app)
    register_visitors_commands(app)
    register_draft_commands(app)
    register_config_commands(app)
