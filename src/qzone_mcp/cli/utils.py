import json
from typing import Any, Dict, List, Optional


def format_output(data: Any, format_type: str = "text") -> str:
    """
    格式化输出数据
    
    Args:
        data: 要格式化的数据
        format_type: 输出格式，支持 text, json, yaml
    
    Returns:
        格式化后的字符串
    """
    if format_type == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)
    elif format_type == "yaml":
        return _to_yaml(data)
    else:
        return _to_text(data)


def _to_text(data: Any) -> str:
    """
    将数据转换为文本格式
    """
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{key}:")
                lines.append(f"  {_to_text(value)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = []
        for i, item in enumerate(data, 1):
            lines.append(f"{i}. {_to_text(item)}")
        return "\n".join(lines)
    else:
        return str(data)


def _to_yaml(data: Any, indent: int = 0) -> str:
    """
    将数据转换为YAML格式（简化版）
    """
    lines = []
    prefix = "  " * indent
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_to_yaml(value, indent + 1))
            elif isinstance(value, str) and "\n" in value:
                lines.append(f'{prefix}{key}: |')
                for line in value.split("\n"):
                    lines.append(f"{prefix}  {line}")
            else:
                lines.append(f"{prefix}{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_to_yaml(item, indent + 1))
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}{data}")
    
    return "\n".join(lines)


def print_table(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> None:
    """
    打印表格
    
    Args:
        data: 数据列表
        headers: 表头列表，默认为数据字典的键
    """
    if not data:
        print("无数据")
        return
    
    if headers is None:
        headers = list(data[0].keys())
    
    max_lengths = []
    for header in headers:
        max_len = len(header)
        for row in data:
            value = str(row.get(header, ""))
            max_len = max(max_len, len(value))
        max_lengths.append(max_len)
    
    format_str = " | ".join(f"{{:<{ml}}}" for ml in max_lengths)
    separator = "-+-".join("-" * ml for ml in max_lengths)
    
    print(format_str.format(*headers))
    print(separator)
    
    for row in data:
        values = [str(row.get(header, "")) for header in headers]
        print(format_str.format(*values))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
    
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def format_config_value(value: Any) -> str:
    """
    格式化配置值用于显示
    
    Args:
        value: 配置值
    
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        return f"[{', '.join(str(v) for v in value)}]"
    elif isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    else:
        return str(value)


def validate_port(port: int) -> None:
    """
    验证端口号是否有效
    
    Args:
        port: 端口号
    
    Raises:
        ValueError: 端口号无效时
    """
    if not isinstance(port, int):
        raise ValueError("端口号必须为整数")
    if port < 1 or port > 65535:
        raise ValueError("端口号必须在1-65535之间")
