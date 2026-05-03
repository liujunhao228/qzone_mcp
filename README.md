# QQ空间 MCP 服务器

让 AI Agent 能够操作 QQ 空间的 MCP (Model Context Protocol) 服务器。

## ⚠️ 免责声明

### 非官方性质声明
本项目为非官方项目，与腾讯公司及其关联公司无任何关联。本项目仅对 Qzone API 进行封装，供 AI Agent 使用，未对 QQ 空间产生实质性替代作用，并禁止商业用途。

### 使用风险提示
1. 使用本项目需遵守 QQ 空间的服务条款和相关法律法规
2. 用户需自行承担因使用本项目而产生的一切风险
3. 频繁操作可能触发 QQ 空间的风控机制，导致账号受限或封禁
4. Cookie 等敏感信息需妥善保管，泄露可能导致账号安全问题

### 责任限制条款
1. 本项目开发者不对因使用本项目而造成的任何直接或间接损失承担责任
2. 本项目开发者不对 QQ 空间服务的可用性、稳定性或安全性提供任何保证
3. 本项目开发者保留随时更新、修改或终止本项目的权利，无需提前通知

### 知识产权声明
1. QQ 空间及其相关服务的知识产权归腾讯公司所有
2. 本项目仅提供 API 封装，不包含任何 QQ 空间的源代码或核心技术
3. 用户在使用本项目时需确保遵守相关知识产权法律法规

### 用户使用规范
1. 禁止将本项目用于商业用途
2. 禁止利用本项目进行恶意攻击、刷量或其他违规操作
3. 禁止泄露或分享他人的 QQ 空间数据
4. 使用本项目即表示同意本免责声明的全部条款

## 功能特性

- 📖 **获取说说列表** - 查看自己或他人的QQ空间说说
- 📝 **发布说说** - 在QQ空间发布新内容，支持图片
- ❤️ **点赞互动** - 为说说点赞
- 💬 **评论功能** - 发表评论和回复评论
- 👥 **访客记录** - 查看访问过你空间的访客
- 👀 **好友动态** - 获取好友空间动态
- 📦 **本地存储** - SQLite数据库持久化保存说说和评论
- 📋 **草稿箱** - 创建、编辑、保存和发布草稿
- 🔄 **自动备份** - 数据库自动备份与恢复
- 🔌 **OneBot集成** - 自动获取Cookie，无需手动配置

## 快速开始

### 1. 安装

```bash
# 使用 uv 安装（推荐）
uv pip install .

# 或者使用 pip
pip install .
```

### 2. 设置配置

创建 `.env` 文件并配置：

```env
# QQ空间配置
QZONE_QZONE__COOKIE=your_qzone_cookie_here
QZONE_QZONE__TIMEOUT=30
QZONE_QZONE__MAX_RETRIES=3

# OneBot配置（可选，自动获取Cookie）
QZONE_ONEBOT__ENABLED=false
QZONE_ONEBOT__PROVIDER=napcat
QZONE_ONEBOT__HOST=127.0.0.1
QZONE_ONEBOT__PORT=3000
```

### 3. 获取QQ空间Cookie

1. 登录 QQ空间网页版：https://qzone.qq.com
2. 打开浏览器开发者工具（F12）
3. 在 **Application > Cookies > user.qzone.qq.com** 中复制所有Cookie

### 4. 启动 MCP 服务器

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

# 草稿箱操作
qzone-cli draft create "我的草稿" --title "草稿标题"
qzone-cli draft publish <draft_id>

# 查看登录状态
qzone-cli auth status
```

### MCP 工具列表

| 工具名称 | 描述 | 读写属性 |
|---------|------|---------|
| `qzone_get_feeds` | 获取说说列表 | 只读 |
| `qzone_get_post_detail` | 获取单条说说详情 | 只读 |
| `qzone_publish_post` | 发布说说 | 可写 |
| `qzone_delete_post` | 删除说说 | 可写 |
| `qzone_like_post` | 点赞说说 | 可写 |
| `qzone_comment_post` | 评论说说 | 可写 |
| `qzone_reply_comment` | 回复评论 | 可写 |
| `qzone_get_visitors` | 获取访客记录 | 只读 |
| `qzone_get_friend_feeds` | 获取好友动态 | 只读 |
| `qzone_save_feed` | 保存说说到本地数据库 | 可写 |
| `qzone_save_feed_with_comments` | 保存说说及评论 | 可写 |
| `qzone_get_saved_feeds` | 获取本地保存的说说列表 | 只读 |
| `qzone_get_saved_feed` | 获取单条本地保存的说说 | 只读 |
| `qzone_delete_saved_feed` | 删除本地保存的说说 | 可写 |
| `qzone_get_saved_feed_count` | 获取本地保存的说说数量 | 只读 |
| `qzone_create_draft` | 创建新草稿 | 可写 |
| `qzone_update_draft` | 更新草稿内容 | 可写 |
| `qzone_get_draft` | 获取草稿详情 | 只读 |
| `qzone_get_drafts` | 获取草稿列表 | 只读 |
| `qzone_delete_draft` | 删除草稿 | 可写 |
| `qzone_preview_draft` | 预览草稿 | 只读 |
| `qzone_publish_draft` | 发布草稿为说说 | 可写 |
| `qzone_get_draft_count` | 获取草稿数量 | 只读 |
| `qzone_backup_database` | 备份数据库 | 可写 |
| `qzone_list_backups` | 获取备份文件列表 | 只读 |
| `qzone_restore_database` | 从备份恢复数据库 | 可写 |
| `qzone_validate_data` | 验证数据完整性 | 只读 |
| `qzone_repair_data` | 修复数据问题 | 可写 |
| `qzone_get_database_stats` | 获取数据库统计信息 | 只读 |
| `qzone_set_cookie` | 设置Cookie | 可写 |
| `qzone_login_status` | 获取登录状态 | 只读 |
| `qzone_check_onebot_status` | 检查OneBot状态 | 只读 |
| `qzone_start_auto_backup` | 启动自动定时备份 | 可写 |
| `qzone_stop_auto_backup` | 停止自动定时备份 | 可写 |

## 项目结构

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
│   │   └── __init__.py
│   ├── parser/                       # 解析器
│   │   ├── json_parser.py            # JSON 响应解析
│   │   ├── html_parser.py            # HTML 页面解析
│   │   └── __init__.py
│   ├── logging/                      # 日志系统
│   │   ├── logger.py                 # 日志记录器
│   │   ├── formatters.py             # 日志格式化器
│   │   └── __init__.py
│   ├── utils/                        # 工具函数
│   ├── exceptions/                   # 异常处理
│   ├── config.py                     # 配置定义
│   ├── server.py                     # MCP 服务器入口
│   ├── cli.py                        # CLI 入口
│   └── __init__.py
├── tests/                           # 测试目录
├── docs/                            # 文档目录
│   └── usage.md                     # 详细使用文档
├── .qzone/                          # 数据存储目录（运行时创建）
│   ├── qzone.db                     # SQLite 数据库文件
│   ├── backups/                     # 备份文件目录
│   └── logs/                        # 日志文件目录
├── pyproject.toml                   # 项目配置
└── README.md                        # 项目说明
```

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
| `QZONE_ONEBOT__API_PATH` | string | /get_cookies | 获取Cookie的API路径 |
| `QZONE_ONEBOT__TOKEN` | string | - | Bearer token（可选） |

### 日志配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `QZONE_LOG__LEVEL` | string | INFO | 日志级别: DEBUG/INFO/WARN/ERROR |
| `QZONE_LOG__MAX_SIZE` | int | 10485760 | 单文件最大字节数(10MB) |
| `QZONE_LOG__BACKUP_COUNT` | int | 5 | 保留的日志备份数 |
| `QZONE_LOG__CONSOLE_ENABLED` | bool | true | 是否输出到控制台 |
| `QZONE_LOG__FILE_ENABLED` | bool | true | 是否输出到文件 |

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

## 贡献代码

- 本项目为Vibe Coding产物，大部分功能迁移自**[astrbot_plugin_qzone](https://github.com/Zhalslar/astrbot_plugin_qzone)**，且未经全面的测试
- 请确保代码符合项目的编码规范和风格
- 请在提交代码前，先运行测试，确保代码质量避免引入新的问题

## 注意事项

1. **登录状态**：所有操作需要有效的QQ空间登录状态
2. **操作频率**：请合理控制操作频率，避免触发风控
3. **敏感操作**：发布、点赞、评论等操作请谨慎使用
4. **Cookie安全**：Cookie包含敏感信息，请妥善保管，不要泄露给他人
5. **数据备份**：建议定期备份数据库，防止数据丢失

## 致谢

本项目的开发参考了以下开源项目和资源，在此表示诚挚的感谢：

- **[CampuxBot](https://github.com/idoknow/CampuxBot)** - 部分代码实现参考了该项目
- **[QQ 空间爬虫之爬取说说](https://kylingit.com/blog/qq-空间爬虫之爬取说说/)** - 感谢该博客提供的技术思路
- **[QzoneExporter](https://github.com/wwwpf/QzoneExporter)** - QQ空间数据导出项目，提供了宝贵的参考
- **[astrbot_plugin_qzone](https://github.com/Zhalslar/astrbot_plugin_qzone)** - AstrBot QQ空间对接插件，本项目的设计灵感来源之一

## 文档

- [详细使用文档](docs/usage.md) - 包含完整的功能说明、API文档和常见问题