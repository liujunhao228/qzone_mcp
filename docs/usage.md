# QQ空间 MCP 服务器使用文档

## 1. 项目概述

### 1.1 项目定位

QQ空间 MCP 服务器是一个基于 **Model Context Protocol (MCP)** 规范实现的服务，旨在为 AI Agent 提供完整的 QQ 空间操作能力。通过该服务，AI 可以像人类一样浏览、发布、互动 QQ 空间内容。

### 1.2 核心价值

- **无缝集成 AI Agent**：通过 MCP 协议与 Claude 等 AI 平台无缝对接
- **完整的 QQ空间功能**：支持说说管理、互动操作、访客记录等全部核心功能
- **本地数据持久化**：自动保存说说、评论等数据到本地数据库
- **智能 Cookie 管理**：支持手动配置和 OneBot 自动获取两种方式
- **草稿箱功能**：支持创建、编辑、保存和发布草稿

### 1.3 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastMCP | 0.1.0+ | MCP 协议实现框架 |
| SQLAlchemy | 2.0+ | 数据库 ORM |
| SQLite | 3.0+ | 本地数据库 |
| aiohttp | 3.9.0+ | HTTP 客户端 |
| Pydantic | 2.0+ | 数据验证 |
| Typer | 0.9+ | 命令行接口 |

---

## 2. 功能特性详解

### 2.1 说说管理

| 功能 | 描述 |
|------|------|
| 获取说说列表 | 支持分页获取自己或他人的说说列表 |
| 获取说说详情 | 获取单条说说的完整信息，包含所有评论 |
| 发布说说 | 支持纯文本和图文混合发布，最多9张图片 |
| 删除说说 | 删除指定的说说 |

### 2.2 互动功能

| 功能 | 描述 |
|------|------|
| 点赞 | 为指定说说点赞 |
| 评论 | 对说说发表评论，支持表情和特殊字符 |
| 回复评论 | 回复指定评论 |

### 2.3 访客记录

- 获取访客列表，包含访客昵称、头像、访问时间等信息
- 支持分页获取，最多每页50条

### 2.4 好友动态

- 获取好友空间动态（需好友空间权限）
- 通过 HTML 解析方式获取最新动态

### 2.5 数据库存储

| 功能 | 描述 |
|------|------|
| 数据持久化 | 自动保存说说、评论、访客等数据到本地 SQLite 数据库 |
| 数据查询 | 支持按条件查询本地存储的数据 |
| 数据备份 | 支持手动和自动备份数据库 |
| 数据恢复 | 从备份文件恢复数据库 |
| 数据验证 | 验证数据库完整性，修复孤儿记录 |

### 2.6 草稿箱

| 功能 | 描述 |
|------|------|
| 创建草稿 | 创建新的说说草稿 |
| 编辑草稿 | 修改已有的草稿内容 |
| 预览草稿 | 查看草稿预览和统计信息 |
| 发布草稿 | 将草稿发布为正式说说 |
| 软删除 | 将草稿标记为已删除（可恢复） |
| 硬删除 | 永久删除草稿 |

---

## 3. 目录结构

```
qzone_mcp/
├── src/qzone_mcp/                    # 源代码目录
│   ├── api/                          # QQ空间 API 模块
│   │   ├── client.py                 # HTTP 客户端封装
│   │   ├── qzone_api.py              # QQ空间 API 实现
│   │   ├── constants.py              # API URL 和常量配置
│   │   └── __init__.py
│   ├── cli/                          # 命令行接口
│   │   ├── commands/                 # CLI 命令实现
│   │   │   ├── auth.py               # 认证相关命令
│   │   │   ├── comment.py            # 评论相关命令
│   │   │   ├── config.py             # 配置管理命令
│   │   │   ├── draft.py              # 草稿箱命令
│   │   │   ├── feeds.py              # 说说相关命令
│   │   │   ├── visitors.py           # 访客相关命令
│   │   │   └── __init__.py
│   │   ├── app.py                    # CLI 应用入口
│   │   ├── errors.py                 # CLI 错误处理
│   │   ├── utils.py                  # CLI 工具函数
│   │   └── __init__.py
│   ├── config_manager/               # 配置管理
│   │   ├── manager.py                # 配置读写管理
│   │   ├── crypto.py                 # 加密解密处理
│   │   ├── schema.py                 # 配置数据模型
│   │   └── __init__.py
│   ├── db/                           # 数据库模块
│   │   ├── manager.py                # 数据库连接管理器
│   │   ├── models.py                 # SQLAlchemy 数据模型
│   │   ├── repository.py             # 数据访问层
│   │   ├── backup.py                 # 数据库备份恢复
│   │   ├── validation.py             # 数据验证修复
│   │   └── __init__.py
│   ├── draft/                        # 草稿箱服务
│   │   ├── service.py                # 草稿业务逻辑
│   │   └── __init__.py
│   ├── session/                      # 会话管理
│   │   ├── session.py                # QzoneSession 类
│   │   ├── provider.py               # OneBot 提供者
│   │   └── __init__.py
│   ├── model/                        # 数据模型
│   │   ├── context.py                # QzoneContext
│   │   ├── feed.py                   # Feed 模型
│   │   ├── response.py               # API 响应模型
│   │   ├── constants.py              # 模型常量
│   │   └── __init__.py
│   ├── parser/                       # 解析器
│   │   ├── json_parser.py            # JSON 响应解析
│   │   ├── html_parser.py            # HTML 页面解析
│   │   └── __init__.py
│   ├── logging/                      # 日志系统
│   │   ├── logger.py                 # 日志记录器
│   │   ├── formatters.py             # 日志格式化器
│   │   ├── context.py                # 日志上下文
│   │   └── __init__.py
│   ├── utils/                        # 工具函数
│   │   ├── image.py                  # 图片处理
│   │   └── __init__.py
│   ├── exceptions/                   # 异常处理
│   │   ├── qzone.py                  # QQ空间相关异常
│   │   └── __init__.py
│   ├── config.py                     # 配置定义
│   ├── server.py                     # MCP 服务器入口
│   ├── cli.py                        # CLI 入口
│   ├── __init__.py
│   └── __main__.py
├── tests/                           # 测试目录
│   ├── unit/                        # 单元测试
│   └── integration/                 # 集成测试
├── .qzone/                          # 数据存储目录（运行时创建）
│   ├── qzone.db                     # SQLite 数据库文件
│   ├── backups/                     # 备份文件目录
│   └── logs/                        # 日志文件目录
├── pyproject.toml                   # 项目配置
├── README.md                        # 项目说明
└── docs/                            # 文档目录
    └── usage.md                     # 详细使用文档
```

---

## 4. 核心模块介绍

### 4.1 API 模块

**职责**：封装 QQ空间 HTTP API，处理请求发送和响应解析

**文件结构**：
- `client.py`：HTTP 客户端，封装 aiohttp，处理 Cookie 注入和重试逻辑
- `qzone_api.py`：QQ空间 API 封装，包含说说、评论、访客等接口
- `constants.py`：API URL 常量和请求参数配置

**核心类**：
- `QzoneHttpClient`：HTTP 客户端类，提供统一的请求接口
- `QzoneAPI`：QQ空间 API 封装类，提供业务级方法

### 4.2 会话管理

**职责**：管理 QQ空间 登录状态，处理 Cookie 获取和刷新

**文件结构**：
- `session.py`：QzoneSession 类，管理会话状态
- `provider.py`：OneBot 提供者工厂，支持 napcat、llonebot 等

**核心类**：
- `QzoneSession`：会话管理类，负责 Cookie 解析、登录状态维护、自动刷新
- `OneBotProvider`：OneBot 客户端封装，自动获取 Cookie

### 4.3 数据库管理

**职责**：提供 SQLite 数据库的异步操作接口

**文件结构**：
- `manager.py`：数据库连接管理器（单例模式）
- `models.py`：SQLAlchemy 数据模型定义
- `repository.py`：数据访问层，封装 CRUD 操作
- `backup.py`：数据库备份和恢复功能
- `validation.py`：数据完整性验证和修复

**数据库模型**：

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `feeds` | 说说数据 | tid, uin, content, images, likes, comments |
| `comments` | 评论数据 | comment_id, tid, uin, content, parent_id |
| `drafts` | 草稿数据 | id, title, content, images, status |
| `visitors` | 访客记录 | uin, nickname, avatar, time |
| `user_profiles` | 用户资料 | uin, nickname, avatar, signature |
| `like_records` | 点赞记录 | tid, uin, time |

### 4.4 草稿箱服务

**职责**：提供草稿的创建、编辑、保存和发布功能

**核心类**：`DraftService`

**主要方法**：
- `create_draft()`：创建新草稿
- `get_draft()`：获取草稿详情
- `update_draft()`：更新草稿内容
- `delete_draft()`：删除草稿（支持软删除和硬删除）
- `publish_draft()`：发布草稿为说说
- `preview_draft()`：预览草稿内容

### 4.5 配置管理

**职责**：管理应用配置，支持多种配置来源

**文件结构**：
- `manager.py`：配置读写管理器
- `crypto.py`：配置加密解密（用于敏感信息如 Cookie）
- `schema.py`：配置数据模型

**配置来源优先级**：
1. `.env` 环境变量文件
2. 配置文件（`~/.qzone/config.json`）
3. 命令行参数

### 4.6 日志系统

**职责**：提供结构化日志记录功能

**特性**：
- 支持控制台和文件双输出
- 自动日志滚动（按文件大小）
- 支持多级别日志（DEBUG/INFO/WARN/ERROR）
- 结构化日志输出（JSON 格式）

---

## 5. 安装与配置

### 5.1 环境要求

- Python 3.10 或更高版本
- 建议使用 `uv` 进行包管理

### 5.2 安装步骤

```bash
# 进入项目目录
cd qzone_mcp

# 使用 uv 安装（推荐）
uv pip install .

# 或者使用 pip
pip install .

# 安装开发依赖（可选）
uv pip install ".[dev]"
```

### 5.3 配置说明

#### 5.3.1 配置方式

**方式一：环境变量文件（.env）**

创建 `.env` 文件：

```env
# QQ空间配置
QZONE_QZONE__COOKIE=your_qzone_cookie_here
QZONE_QZONE__TIMEOUT=30
QZONE_QZONE__MAX_RETRIES=3
QZONE_QZONE__RETRY_DELAY=2

# OneBot配置（可选，自动获取Cookie）
QZONE_ONEBOT__ENABLED=false
QZONE_ONEBOT__PROVIDER=napcat
QZONE_ONEBOT__HOST=127.0.0.1
QZONE_ONEBOT__PORT=3000
QZONE_ONEBOT__TIMEOUT=10
QZONE_ONEBOT__API_PATH=/get_cookies

# 日志配置
QZONE_LOG__LEVEL=INFO
QZONE_LOG__MAX_SIZE=10485760
QZONE_LOG__BACKUP_COUNT=5

# 数据目录
QZONE_DATA_DIR=~/.qzone

# 管理员列表（可选）
QZONE_ADMINS=["123456789"]
```

**方式二：配置文件**

配置文件位于 `~/.qzone/config.json`，由系统自动创建和管理。

#### 5.3.2 配置项详解

**QQ空间配置**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `QZONE_QZONE__COOKIE` | string | - | QQ空间 Cookie 字符串 |
| `QZONE_QZONE__TIMEOUT` | int | 30 | 请求超时时间（秒） |
| `QZONE_QZONE__MAX_RETRIES` | int | 3 | 最大重试次数 |
| `QZONE_QZONE__RETRY_DELAY` | int | 2 | 重试延迟（秒） |

**OneBot 配置**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `QZONE_ONEBOT__ENABLED` | bool | false | 是否启用 OneBot 自动获取 Cookie |
| `QZONE_ONEBOT__PROVIDER` | string | napcat | OneBot 类型：napcat/llonebot/generic |
| `QZONE_ONEBOT__HOST` | string | 127.0.0.1 | 服务地址 |
| `QZONE_ONEBOT__PORT` | int | 3000 | HTTP 端口 |
| `QZONE_ONEBOT__TIMEOUT` | int | 10 | 请求超时时间 |
| `QZONE_ONEBOT__API_PATH` | string | /get_cookies | 获取 Cookie 的 API 路径 |
| `QZONE_ONEBOT__TOKEN` | string | - | Bearer token（可选） |

**日志配置**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `QZONE_LOG__LEVEL` | string | INFO | 日志级别 |
| `QZONE_LOG__PATH` | string | ~/.qzone/logs | 日志存储目录 |
| `QZONE_LOG__MAX_SIZE` | int | 10485760 | 单文件最大字节数（10MB） |
| `QZONE_LOG__BACKUP_COUNT` | int | 5 | 保留的日志备份数 |
| `QZONE_LOG__CONSOLE_ENABLED` | bool | true | 是否输出到控制台 |
| `QZONE_LOG__FILE_ENABLED` | bool | true | 是否输出到文件 |

### 5.4 Cookie 获取方法

**方法一：浏览器获取**

1. 登录 QQ空间网页版：https://qzone.qq.com
2. 打开浏览器开发者工具（F12）
3. 在 **Application > Cookies > user.qzone.qq.com** 中复制所有 Cookie
4. 将复制的 Cookie 字符串设置到配置中

**方法二：OneBot 自动获取（推荐）**

配置 OneBot 客户端后，系统会自动获取并更新 Cookie：

```env
QZONE_ONEBOT__ENABLED=true
QZONE_ONEBOT__PROVIDER=napcat
QZONE_ONEBOT__HOST=127.0.0.1
QZONE_ONEBOT__PORT=3000
```

---

## 6. 使用方法

### 6.1 命令行工具

#### 6.1.1 获取说说列表

```bash
# 获取自己的说说
qzone-cli feeds

# 获取指定用户的说说
qzone-cli feeds --user 123456789

# 指定获取数量
qzone-cli feeds --num 20

# 获取完整详情（包含评论）
qzone-cli feeds --detail
```

#### 6.1.2 发布说说

```bash
# 发布纯文本说说
qzone-cli publish "今天天气真好！"

# 发布带图片的说说
qzone-cli publish "风景真美" --image https://example.com/img1.jpg --image https://example.com/img2.jpg
```

#### 6.1.3 点赞和评论

```bash
# 点赞说说
qzone-cli like --tid 123456789 --author 123456789

# 评论说说
qzone-cli comment --tid 123456789 --author 123456789 --content "说得好！"
```

#### 6.1.4 获取访客记录

```bash
# 获取访客列表
qzone-cli visitors

# 获取指定页数
qzone-cli visitors --page 2
```

#### 6.1.5 草稿箱操作

```bash
# 创建草稿
qzone-cli draft create "我的草稿内容" --title "草稿标题"

# 查看草稿列表
qzone-cli draft list

# 查看草稿详情
qzone-cli draft get <draft_id>

# 更新草稿
qzone-cli draft update <draft_id> --content "新内容"

# 发布草稿
qzone-cli draft publish <draft_id>

# 删除草稿
qzone-cli draft delete <draft_id>
```

#### 6.1.6 配置管理

```bash
# 查看当前配置
qzone-cli config show

# 设置 Cookie
qzone-cli config set-cookie "your_cookie_here"

# 检查登录状态
qzone-cli auth status

# 检查 OneBot 状态
qzone-cli auth check-onebot
```

### 6.2 MCP 服务器启动

```bash
# 启动 MCP 服务器
qzone-mcp

# 使用 uvx 运行
uvx qzone-mcp
```

### 6.3 Claude AI 配置

在 Claude AI 中添加此 MCP 服务器时，使用以下配置：

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

---

## 7. MCP 工具列表详解

### 7.1 说说管理工具

#### `qzone_get_feeds` - 获取说说列表

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_id` | string | 否 | 空（当前用户） | 目标用户QQ号 |
| `pos` | int | 否 | 0 | 起始位置（分页） |
| `num` | int | 否 | 5 | 获取数量（1-50） |
| `with_detail` | bool | 否 | false | 是否包含完整评论 |

**返回示例**：
```json
{
  "result": [
    {
      "tid": "123456789",
      "uin": 123456789,
      "nickname": "张三",
      "content": "今天天气真好！",
      "likes": 10,
      "comments": 3,
      "time": "2024-01-15 10:30"
    }
  ]
}
```

#### `qzone_get_post_detail` - 获取说说详情

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |
| `author_uin` | int | 是 | 作者QQ号 |

**返回示例**：
```json
{
  "result": {
    "tid": "123456789",
    "uin": 123456789,
    "nickname": "张三",
    "content": "今天天气真好！",
    "likes": 10,
    "comments": 3,
    "comment_list": [
      {"id": "c1", "uin": 987654321, "nickname": "李四", "content": "确实不错！"}
    ]
  }
}
```

#### `qzone_publish_post` - 发布说说

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 说说内容（最大2000字） |
| `image_urls` | list | 否 | 图片URL列表（最多9张） |

**返回示例**：
```json
{
  "result": {
    "success": true,
    "tid": "123456789",
    "message": "发布成功"
  }
}
```

#### `qzone_delete_post` - 删除说说

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |

**返回示例**：
```json
{
  "result": {
    "success": true,
    "message": "删除成功"
  }
}
```

### 7.2 互动功能工具

#### `qzone_like_post` - 点赞说说

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |
| `author_uin` | int | 是 | 作者QQ号 |

**返回示例**：
```json
{
  "result": {
    "success": true,
    "message": "点赞成功"
  }
}
```

#### `qzone_comment_post` - 评论说说

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |
| `author_uin` | int | 是 | 作者QQ号 |
| `content` | string | 是 | 评论内容（最大500字） |

**返回示例**：
```json
{
  "result": {
    "success": true,
    "comment_id": "c123456",
    "message": "评论成功"
  }
}
```

#### `qzone_reply_comment` - 回复评论

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |
| `author_uin` | int | 是 | 作者QQ号 |
| `comment_id` | string | 是 | 要回复的评论ID |
| `content` | string | 是 | 回复内容（最大500字） |

**返回示例**：
```json
{
  "result": {
    "success": true,
    "comment_id": "r123456",
    "message": "回复成功"
  }
}
```

### 7.3 访客记录工具

#### `qzone_get_visitors` - 获取访客记录

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | int | 否 | 1 | 页码 |
| `num` | int | 否 | 20 | 每页数量（1-50） |

**返回示例**：
```markdown
## 访客记录

| 访客 | 来源 | 状态 | 访问时间 |
|------|------|------|----------|
| 李四 | QQ空间 | 好友 | 2024-01-15 14:30 |
| 王五 | 搜索 | 陌生人 | 2024-01-15 13:20 |
```

### 7.4 好友动态工具

#### `qzone_get_friend_feeds` - 获取好友动态

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `pos` | int | 否 | 0 | 起始位置 |
| `num` | int | 否 | 5 | 获取数量（1-50） |

**返回示例**：
```json
{
  "result": [
    {
      "tid": "123456789",
      "uin": 987654321,
      "nickname": "李四",
      "content": "今天出去玩了！",
      "time": "2024-01-15 14:30"
    }
  ]
}
```

### 7.5 数据库操作工具

#### `qzone_save_feed` - 保存说说到数据库

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |
| `uin` | int | 是 | 发布者QQ号 |
| `content` | string | 是 | 说说内容 |
| `nickname` | string | 否 | 发布者昵称 |
| `images` | string | 否 | 图片URL列表（JSON格式） |
| `likes` | int | 否 | 点赞数 |
| `comments` | int | 否 | 评论数 |
| `shares` | int | 否 | 分享数 |
| `time` | string | 否 | 发布时间 |
| `is_liked` | bool | 否 | 是否已点赞 |

#### `qzone_get_saved_feeds` - 获取本地保存的说说列表

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `uin` | int | 否 | 空（全部） | 发布者QQ号 |
| `limit` | int | 否 | 20 | 返回数量 |
| `offset` | int | 否 | 0 | 偏移量 |

#### `qzone_get_saved_feed` - 获取单条本地说说

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |

#### `qzone_delete_saved_feed` - 删除本地说说

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tid` | string | 是 | 说说ID |

### 7.6 草稿箱工具

#### `qzone_create_draft` - 创建草稿

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | 是 | 草稿内容 |
| `title` | string | 否 | 草稿标题 |
| `images` | string | 否 | 图片URL列表（JSON格式） |

**返回示例**：
```json
{
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "我的草稿",
    "content": "今天天气真好！",
    "status": "draft",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

#### `qzone_update_draft` - 更新草稿

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `draft_id` | string | 是 | 草稿ID |
| `content` | string | 否 | 新内容 |
| `title` | string | 否 | 新标题 |
| `images` | string | 否 | 新图片列表（JSON格式） |

#### `qzone_get_draft` - 获取草稿详情

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `draft_id` | string | 是 | 草稿ID |

#### `qzone_get_drafts` - 获取草稿列表

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | 否 | 空（全部） | 状态过滤（draft/published/deleted） |
| `limit` | int | 否 | 20 | 返回数量 |
| `offset` | int | 否 | 0 | 偏移量 |

#### `qzone_delete_draft` - 删除草稿

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `draft_id` | string | 是 | - | 草稿ID |
| `hard_delete` | bool | 否 | false | 是否硬删除 |

#### `qzone_publish_draft` - 发布草稿

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `draft_id` | string | 是 | 草稿ID |

#### `qzone_preview_draft` - 预览草稿

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `draft_id` | string | 是 | 草稿ID |

**返回示例**：
```json
{
  "result": {
    "draft_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "我的草稿",
    "content_preview": "今天天气真好！",
    "content_length": 8,
    "image_count": 0,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00",
    "status": "draft"
  }
}
```

### 7.7 数据备份工具

#### `qzone_backup_database` - 备份数据库

**返回示例**：
```json
{
  "result": {
    "success": true,
    "message": "备份成功",
    "backup_path": "/home/user/.qzone/backups/qzone_backup_20240115_103000.db"
  }
}
```

#### `qzone_list_backups` - 获取备份列表

**返回示例**：
```json
{
  "result": [
    {
      "filename": "qzone_backup_20240115_103000.db",
      "path": "/home/user/.qzone/backups/qzone_backup_20240115_103000.db",
      "size": 102400,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### `qzone_restore_database` - 恢复数据库

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `backup_filename` | string | 是 | 备份文件名 |

### 7.8 数据验证工具

#### `qzone_validate_data` - 验证数据完整性

**返回示例**：
```json
{
  "result": {
    "status": "success",
    "tables": {
      "feeds": {"valid": true, "count": 100, "issues": []},
      "comments": {"valid": true, "count": 500, "issues": []}
    },
    "issues": [],
    "summary": {
      "total_tables": 6,
      "valid_tables": 6,
      "total_issues": 0
    }
  }
}
```

#### `qzone_repair_data` - 修复数据问题

**返回示例**：
```json
{
  "result": {
    "status": "success",
    "deleted": {
      "comments": 0,
      "like_records": 0
    },
    "errors": []
  }
}
```

#### `qzone_get_database_stats` - 获取数据库统计

**返回示例**：
```json
{
  "result": {
    "feeds": 100,
    "comments": 500,
    "drafts": 10,
    "visitors": 200,
    "user_profiles": 50,
    "like_records": 300
  }
}
```

### 7.9 服务器管理工具

#### `qzone_set_cookie` - 设置 Cookie

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cookie_string` | string | 是 | QQ空间 Cookie 字符串 |

**返回示例**：
```json
{
  "result": {
    "message": "Cookie设置成功"
  }
}
```

#### `qzone_login_status` - 获取登录状态

**返回示例**：
```json
{
  "result": {
    "logged_in": true,
    "uin": 123456789
  }
}
```

#### `qzone_check_onebot_status` - 检查 OneBot 状态

**返回示例**：
```json
{
  "result": {
    "connected": true,
    "enabled": true,
    "provider": "llonebot",
    "host": "127.0.0.1",
    "port": 3000,
    "has_cookies": true,
    "token_enabled": true,
    "message": "连接成功，已获取Cookie"
  }
}
```

#### `qzone_start_auto_backup` - 启动自动定时备份

**说明**：启动自动定时备份任务（每24小时备份一次）

**返回示例**：
```json
{
  "result": {
    "success": true,
    "message": "自动备份已启动"
  }
}
```

#### `qzone_stop_auto_backup` - 停止自动定时备份

**说明**：停止自动定时备份任务

**返回示例**：
```json
{
  "result": {
    "success": true,
    "message": "自动备份已停止"
  }
}
```

---

## 8. 数据库功能

### 8.1 数据持久化

系统会自动将以下数据保存到本地 SQLite 数据库：

| 数据类型 | 保存时机 | 说明 |
|----------|----------|------|
| 说说 | 通过 `qzone_save_feed` 工具手动保存 | 包含内容、图片、点赞数等 |
| 评论 | 保存说说时可一并保存 | 包含评论内容、评论者信息 |
| 草稿 | 创建/更新草稿时自动保存 | 包含标题、内容、图片 |
| 访客 | 获取访客记录时可保存 | 包含访客基本信息 |

### 8.2 备份与恢复

**自动备份**：系统每天自动备份一次数据库

**手动备份**：
```bash
# 使用 CLI 命令
qzone-cli backup

# 使用 MCP 工具
# 调用 qzone_backup_database
```

**恢复备份**：
```bash
# 使用 CLI 命令
qzone-cli restore <backup_filename>

# 使用 MCP 工具
# 调用 qzone_restore_database
```

### 8.3 数据验证与修复

**验证数据完整性**：
```bash
qzone-cli validate
```

**修复数据问题**：
```bash
qzone-cli repair
```

---

## 9. 常见问题及解决方案

### 9.1 登录问题

#### 问题 1：Cookie 无效或过期

**现象**：
```
登录失效，请使用 qzone_set_cookie 工具重新设置Cookie
```

**解决方案**：
1. 重新登录 QQ空间网页版
2. 在浏览器开发者工具中获取最新的 Cookie
3. 使用 `qzone_set_cookie` 工具或 `qzone-cli config set-cookie` 命令更新 Cookie

#### 问题 2：Cookie 解析失败

**现象**：
```
Cookie解析失败：请确保Cookie包含uin、skey、p_skey字段
```

**解决方案**：
- 确保复制的 Cookie 包含以下关键字段：
  - `uin`：QQ号
  - `skey`：会话密钥
  - `p_skey`：持久化会话密钥

#### 问题 3：OneBot 连接失败

**现象**：
```
连接失败: Connection refused
```

**解决方案**：
1. 确认 OneBot 客户端已启动
2. 检查配置的 `host` 和 `port` 是否正确
3. 确认 OneBot 服务监听的端口与配置一致
4. 如果启用了 token 验证，确保配置了正确的 token

### 9.2 权限问题

#### 问题 1：无法访问他人空间

**现象**：
```
获取说说失败：权限不足
```

**解决方案**：
- 目标用户的 QQ空间可能设置了访问权限
- 尝试使用对方的好友账号登录

#### 问题 2：无法发布说说

**现象**：
```
发布失败：操作受限
```

**解决方案**：
- 检查账号是否被风控限制
- 降低操作频率
- 尝试在网页版手动发布一条说说验证账号状态

### 9.3 网络问题

#### 问题 1：请求超时

**现象**：
```
获取说说失败：TimeoutError
```

**解决方案**：
1. 检查网络连接
2. 增加超时时间配置（`QZONE_QZONE__TIMEOUT`）
3. 检查 QQ空间服务器是否正常

#### 问题 2：请求被拒绝

**现象**：
```
获取说说失败：403 Forbidden
```

**解决方案**：
- 检查 Cookie 是否有效
- 尝试更换网络环境
- 可能触发了风控，稍后再试

### 9.4 数据库问题

#### 问题 1：数据库文件不存在

**现象**：
```
保存说说失败：database is locked
```

**解决方案**：
- 确保只有一个进程访问数据库
- 检查是否有其他程序占用数据库文件

#### 问题 2：数据库损坏

**现象**：
```
获取本地说说失败：database disk image is malformed
```

**解决方案**：
1. 从备份恢复数据库：`qzone-cli restore <backup_file>`
2. 如果没有备份，尝试修复：
```bash
sqlite3 ~/.qzone/qzone.db "PRAGMA integrity_check;"
```

### 9.5 其他问题

#### 问题 1：说说内容为空

**现象**：发布说说时提示内容不能为空

**解决方案**：
- 确保 `text` 参数不为空且长度大于0
- 检查是否有不可见字符导致内容被截断

#### 问题 2：图片上传失败

**现象**：
```
发布失败：图片上传失败
```

**解决方案**：
1. 检查图片 URL 是否有效
2. 确保图片大小不超过限制
3. 尝试减少图片数量（最多9张）

---

## 附录：工具分类汇总

| 类别 | 工具名称 | 读写属性 |
|------|----------|----------|
| **说说管理** | `qzone_get_feeds` | 只读 |
| | `qzone_get_post_detail` | 只读 |
| | `qzone_publish_post` | 可写 |
| | `qzone_delete_post` | 可写 |
| **互动功能** | `qzone_like_post` | 可写 |
| | `qzone_comment_post` | 可写 |
| | `qzone_reply_comment` | 可写 |
| **访客记录** | `qzone_get_visitors` | 只读 |
| **好友动态** | `qzone_get_friend_feeds` | 只读 |
| **数据库操作** | `qzone_save_feed` | 可写 |
| | `qzone_save_feed_with_comments` | 可写 |
| | `qzone_get_saved_feeds` | 只读 |
| | `qzone_get_saved_feed` | 只读 |
| | `qzone_delete_saved_feed` | 可写 |
| | `qzone_get_saved_feed_count` | 只读 |
| **草稿箱** | `qzone_create_draft` | 可写 |
| | `qzone_update_draft` | 可写 |
| | `qzone_get_draft` | 只读 |
| | `qzone_get_drafts` | 只读 |
| | `qzone_delete_draft` | 可写 |
| | `qzone_preview_draft` | 只读 |
| | `qzone_publish_draft` | 可写 |
| | `qzone_get_draft_count` | 只读 |
| **数据备份** | `qzone_backup_database` | 可写 |
| | `qzone_list_backups` | 只读 |
| | `qzone_restore_database` | 可写 |
| **数据验证** | `qzone_validate_data` | 只读 |
| | `qzone_repair_data` | 可写 |
| | `qzone_get_database_stats` | 只读 |
| **服务器管理** | `qzone_set_cookie` | 可写 |
| | `qzone_login_status` | 只读 |
| | `qzone_check_onebot_status` | 只读 |