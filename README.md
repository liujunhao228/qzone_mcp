# QQ空间 MCP 服务器

让 AI Agent 能够操作 QQ 空间的 MCP (Model Context Protocol) 服务器。

## 功能特性

- 📖 **获取说说列表** - 查看自己或他人的QQ空间说说
- 📝 **发布说说** - 在QQ空间发布新内容，支持图片
- ❤️ **点赞互动** - 为说说点赞
- 💬 **评论功能** - 发表评论和回复评论
- 👥 **访客记录** - 查看访问过你空间的访客

## 安装

```bash
# 使用 uv 安装（推荐）
uv pip install .

# 或者使用 pip
pip install .
```

## 快速开始

### 1. 设置配置

复制 `.env` 文件并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的 QQ空间 Cookie：

```env
# QQ空间配置
QZONE_QZONE__COOKIE=your_qzone_cookie_here
QZONE_QZONE__TIMEOUT=30

# OneBot配置（可选，自动获取Cookie）
QZONE_ONEBOT__ENABLED=true
QZONE_ONEBOT__PROVIDER=llonebot
QZONE_ONEBOT__HOST=127.0.0.1
QZONE_ONEBOT__PORT=3000
```

### 2. 获取QQ空间Cookie

1. 登录 QQ空间网页版：https://qzone.qq.com
2. 打开浏览器开发者工具（F12）
3. 在 **Application > Cookies > user.qzone.qq.com** 中复制所有Cookie

### 3. 启动 MCP 服务器

```bash
qzone-mcp
```

## 使用方法

### 命令行工具

```bash
# 获取说说列表
qzone-cli feeds --user 123456789 --num 10

# 发布说说
qzone-cli publish --text "今天天气真好！"

# 点赞说说
qzone-cli like --tid 123456789 --author 123456789

# 评论说说
qzone-cli comment --tid 123456789 --author 123456789 --content "说得好！"

# 获取访客记录
qzone-cli visitors

# 查看登录状态
qzone-cli status
```

### MCP 工具列表

| 工具名称 | 描述 | 读写属性 |
|---------|------|---------|
| `qzone_get_feeds` | 获取说说列表 | 只读 |
| `qzone_get_post_detail` | 获取单条说说详情 | 只读 |
| `qzone_publish_post` | 发布说说 | 可写 |
| `qzone_like_post` | 点赞说说 | 可写 |
| `qzone_comment_post` | 评论说说 | 可写 |
| `qzone_reply_comment` | 回复评论 | 可写 |
| `qzone_get_visitors` | 获取访客记录 | 只读 |
| `qzone_set_cookie` | 设置Cookie | 可写 |
| `qzone_login_status` | 获取登录状态 | 只读 |
| `qzone_check_onebot_status` | 检查OneBot状态 | 只读 |

## 配置说明

### QQ空间配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `QZONE_QZONE__COOKIE` | string | - | QQ空间Cookie |
| `QZONE_QZONE__TIMEOUT` | int | 30 | 请求超时时间(秒) |
| `QZONE_QZONE__MAX_RETRIES` | int | 3 | 最大重试次数 |
| `QZONE_QZONE__RETRY_DELAY` | int | 2 | 重试延迟(秒) |

### OneBot配置（可选）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `QZONE_ONEBOT__ENABLED` | bool | false | 是否启用OneBot自动获取Cookie |
| `QZONE_ONEBOT__PROVIDER` | string | napcat | OneBot类型: napcat, llonebot, generic |
| `QZONE_ONEBOT__HOST` | string | 127.0.0.1 | 服务地址 |
| `QZONE_ONEBOT__PORT` | int | 3000 | HTTP端口 |
| `QZONE_ONEBOT__TIMEOUT` | int | 10 | 超时时间 |

## 项目结构

```
qzone_mcp/
├── src/qzone_mcp/
│   ├── api/           # QQ空间API客户端
│   │   ├── client.py  # HTTP客户端
│   │   ├── model.py   # 数据模型
│   │   └── session.py # 会话管理
│   ├── cli.py         # 命令行接口
│   ├── config.py      # 配置管理
│   ├── server.py      # MCP服务器
│   └── __main__.py    # 入口文件
├── tests/             # 测试文件
├── .env               # 环境变量配置
├── pyproject.toml     # 项目配置
└── README.md          # 项目说明
```

## MCP 配置（NPX/UVX）

### 使用 UVX 运行

```bash
uvx qzone-mcp
```

### Claude AI 配置 JSON

在 Claude AI 中添加此 MCP 服务器时，使用以下标准配置：

```json
{
  "name": "qzone-mcp",
  "command": "uvx",
  "args": ["qzone-mcp"],
  "env": {
    "QZONE_QZONE__COOKIE": "your_qzone_cookie_here",
    "QZONE_ONEBOT__ENABLED": "false"
  },
  "type": "mcp",
  "description": "QQ空间操作工具集 - 提供完整的QQ空间功能支持",
  "connection": {
    "type": "stdio"
  }
}
```

### 配置字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | MCP服务器名称，用于标识 |
| `command` | string | 是 | 启动命令（uvx 或 npx） |
| `args` | array | 是 | 命令参数数组 |
| `env` | object | 否 | 环境变量配置 |
| `type` | string | 是 | 固定值：`mcp` |
| `description` | string | 否 | 服务器描述 |
| `connection` | object | 否 | 连接配置，默认为stdio |

**注意**：`tool_list` 字段不需要手动配置，MCP服务器启动后会自动向Claude注册工具列表。

### 完整环境变量配置

```json
{
  "env": {
    "QZONE_QZONE__COOKIE": "",
    "QZONE_QZONE__TIMEOUT": "30",
    "QZONE_QZONE__MAX_RETRIES": "3",
    "QZONE_QZONE__RETRY_DELAY": "2",
    "QZONE_ONEBOT__ENABLED": "false",
    "QZONE_ONEBOT__PROVIDER": "napcat",
    "QZONE_ONEBOT__HOST": "127.0.0.1",
    "QZONE_ONEBOT__PORT": "3000",
    "QZONE_ONEBOT__TIMEOUT": "10",
    "QZONE_ONEBOT__API_PATH": "/get_cookies",
    "QZONE_DATA_DIR": "~/.qzone",
    "QZONE_LOG_LEVEL": "INFO",
    "QZONE_ADMINS": "[\"123456789\"]"
  }
}
```

## 测试

```bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit/

# 运行集成测试
uv run pytest tests/integration/
```

## 许可证

MIT License

## 注意事项

1. **登录状态**：所有操作需要有效的QQ空间登录状态
2. **操作频率**：请合理控制操作频率，避免触发风控
3. **敏感操作**：发布、点赞、评论等操作请谨慎使用
4. **Cookie安全**：Cookie包含敏感信息，请妥善保管，不要泄露给他人