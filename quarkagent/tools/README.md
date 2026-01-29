# QuarkAgent Tools

QuarkAgent 工具库提供了一系列实用工具，帮助开发者在 AI 助手应用中快速集成各种功能。这些工具覆盖了文件操作、系统管理、网络请求、计算等多个领域。

## 工具分类

### 1. 代码/文件操作工具 (`code_tools.py`)
提供对文件和代码的基本操作功能：

- **read**: 读取文件内容，支持指定行范围
- **write**: 向文件写入内容
- **edit**: 编辑文件内容，支持替换操作
- **glob**: 搜索匹配特定模式的文件
- **grep**: 在文件中搜索匹配正则表达式的内容
- **bash**: 执行 shell 命令

### 2. 基础工具 (`basic_tools.py`)
提供系统管理、网络请求、剪贴板操作等基础功能：

- **计算器工具**:
  - `calculator`: 计算数学表达式
  - `calculate`: 安全计算数学表达式（支持更多函数）

- **系统信息工具**:
  - `get_current_time`: 获取当前时间
  - `get_system_info`: 获取系统详细信息
  - `system_load`: 获取系统负载信息（CPU、内存、磁盘）
  - `disk_usage`: 获取磁盘使用情况
  - `process_list`: 获取运行中的进程列表

- **文件操作工具**:
  - `file_status`: 分析目录中的文件状态和统计信息

- **网络工具**:
  - `web_search`: 使用 DuckDuckGo 搜索网页（需要 SERPAPI_KEY）
  - `http_request`: 发送 HTTP 请求
  - `open_browser`: 打开网页浏览器

- **应用程序工具**:
  - `open_app`: 打开应用程序
  - `clipboard_copy`: 复制文本到剪贴板

- **文档工具**:
  - `create_docx`: 创建 Word 文档（需要 python-docx 库）

- **环境变量工具**:
  - `env_get`: 获取环境变量值
  - `env_set`: 设置环境变量值

### 3. 计算器工具 (`caculator.py`)
专门的数学计算工具：
- `calculate`: 安全计算数学表达式，支持多种数学函数

## 工具注册与使用

所有工具都使用 `@register_tool` 装饰器进行注册，可以通过以下方式使用：

```python
from quarkagent.tools import (
    get_registered_tools,
    get_tool,
    execute_tool,
    get_tools_description
)

# 获取所有注册的工具
tools = get_registered_tools()

# 执行工具
result = execute_tool('read', path='example.txt', offset=1, limit=10)

# 获取工具描述（用于 AI 助手理解工具功能）
descriptions = get_tools_description()
```

## 安装依赖

部分工具需要额外的依赖库：

```bash
pip install psutil requests python-docx
```

## 环境变量

- **SERPAPI_KEY**: 使用 `web_search` 工具需要设置此环境变量，可从 [SerpAPI](https://serpapi.com/) 获取

## 工具使用示例

### 读取文件
```python
result = execute_tool('read', path='/path/to/file.txt', offset=1, limit=50)
```

### 执行数学计算
```python
result = execute_tool('calculate', expression='2 + 3 * 4')
```

### 搜索文件
```python
result = execute_tool('glob', pattern='*.py', path='/path/to/directory')
```

### 网页搜索
```python
import os
os.environ['SERPAPI_KEY'] = 'your-api-key'
result = execute_tool('web_search', query='Python programming', num_results=5)
```

## 开发说明

- 所有工具函数必须使用 `@register_tool` 装饰器注册
- 工具函数应具有清晰的文档字符串，说明功能、参数和返回值
- 工具函数应处理异常情况，并返回友好的错误信息
- 工具函数应使用 `logging` 模块记录操作信息

## 目录结构

```
quarkagent/tools/
├── __init__.py          # 工具注册和管理模块
├── basic_tools.py       # 基础工具
├── code_tools.py        # 代码/文件操作工具
├── caculator.py         # 计算器工具
└── README.md            # 工具说明文档
```