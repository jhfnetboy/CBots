# CBots 部署指南

本文档提供了在不同平台上部署 CBots 的详细指南，包括 Vercel、Netlify 和 PythonAnywhere。

## 1. 代码准备

无论选择哪种部署方式，都需要先准备好代码：

1. 克隆仓库
```bash
git clone https://github.com/yourusername/CBots.git
cd CBots
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 确保所有环境变量已经正确设置（见下方环境变量部分）

## 2. 环境变量

所有部署方法都需要设置以下环境变量：

```
# Telegram 配置
TELEGRAM_API_ID=你的API_ID
TELEGRAM_API_HASH=你的API_HASH
TELEGRAM_BOT_TOKEN=你的BOT_TOKEN
TELEGRAM_CHANNEL=@你的频道名
TELEGRAM_GROUP=@你的群组名

# Twitter 配置（如果需要）
TWITTER_API_KEY=你的API Key
TWITTER_API_SECRET=你的API Secret
TWITTER_ACCESS_TOKEN=你的Access Token
TWITTER_ACCESS_TOKEN_SECRET=你的Access Token Secret
TWITTER_BEARER_TOKEN=你的Bearer Token
```

## 3. Vercel 部署

Vercel 适合部署 Web 前端和 API 服务，但不适合长期运行的 Python 后台程序。因此，对于 CBots 这样的应用，需要做一些架构调整：

### 3.1 架构调整

1. 分离前端和后端
   - 前端（HTML、CSS、JS）可以部署在 Vercel
   - 后端（Python Telegram Bot）需要部署在支持后台长期运行的服务器上

2. 创建 API 接口
   - 在 Vercel 上部署 API 路由，用于接收前端请求
   - API 将请求转发给实际运行 Bot 的后端服务器

### 3.2 Vercel 部署步骤

1. 安装 Vercel CLI
```bash
npm install -g vercel
```

2. 创建 `vercel.json` 配置文件
```json
{
  "version": 2,
  "builds": [
    { "src": "web_service.py", "use": "@vercel/python" },
    { "src": "static/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "/static/$1" },
    { "src": "/(.*)", "dest": "web_service.py" }
  ]
}
```

3. 部署到 Vercel
```bash
vercel
```

**注意：** Vercel 不适合运行长期后台进程，所以 `main.py` 和 Telegram Bot 核心功能需要部署在其他服务器上。前端部署在 Vercel 后，需要配置 API 请求指向实际运行 Bot 的服务器。

## 4. Netlify 部署

与 Vercel 类似，Netlify 主要适合部署静态网站和无服务器函数，而不是长期运行的后台程序。

### 4.1 架构调整

与 Vercel 相同，需要分离前端和后端，并使用 API 接口连接。

### 4.2 Netlify 部署步骤

1. 安装 Netlify CLI
```bash
npm install -g netlify-cli
```

2. 创建 `netlify.toml` 配置文件
```toml
[build]
  publish = "templates"
  command = "# 没有构建命令"

[functions]
  directory = "netlify/functions"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
```

3. 创建 Netlify 函数目录和文件
```bash
mkdir -p netlify/functions
```

4. 将 API 路由转换为 Netlify 函数，例如创建 `netlify/functions/send_message.js`：
```javascript
const fetch = require('node-fetch');

exports.handler = async function(event, context) {
  // 从请求中获取数据
  const data = JSON.parse(event.body);
  
  // 向实际的 Bot 服务器发送请求
  const response = await fetch('https://your-bot-server.com/api/send_message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  const result = await response.json();
  
  return {
    statusCode: 200,
    body: JSON.stringify(result)
  };
};
```

5. 部署到 Netlify
```bash
netlify deploy --prod
```

**注意：** 与 Vercel 类似，需要额外的服务器运行 Bot 后台程序。

## 5. PythonAnywhere 部署

PythonAnywhere 是最适合部署 CBots 的选项，因为它支持后台长期运行的 Python 程序。

### 5.1 PythonAnywhere 部署步骤

1. 注册并登录 [PythonAnywhere](https://www.pythonanywhere.com/)

2. 打开 Bash 控制台，克隆仓库
```bash
git clone https://github.com/yourusername/CBots.git
cd CBots
```

3. 创建虚拟环境并安装依赖
```bash
mkvirtualenv --python=python3.8 cbots-env
pip install -r requirements.txt
```

4. 创建 Web 应用
   - 在 PythonAnywhere 仪表板中点击 "Web" 选项卡
   - 点击 "Add a new web app"
   - 选择 "Manual configuration" 和 Python 3.8
   - 设置源代码目录为 `/home/yourusername/CBots`
   - 设置 WSGI 配置文件，将路径指向 `web_service.py`

5. 设置环境变量
   - 编辑 WSGI 配置文件，在顶部添加环境变量：
   ```python
   import os
   os.environ['TELEGRAM_API_ID'] = 'your_api_id'
   os.environ['TELEGRAM_API_HASH'] = 'your_api_hash'
   # 添加其他环境变量
   ```

6. 创建 Always-On 任务（需要付费账户）
   - 在 PythonAnywhere 仪表板中点击 "Tasks" 选项卡
   - 添加一个新的 Always-On 任务：
   ```bash
   cd ~/CBots && python main.py
   ```

7. 启动 Web 应用
   - 回到 "Web" 选项卡，点击 "Reload" 启动 Web 应用

### 5.2 PythonAnywhere 优势

- 支持后台长期运行的 Python 程序
- 提供 Web 应用托管
- 有免费套餐可用于测试（但有资源限制）
- 付费版提供 Always-On 任务，确保 Bot 始终在线

## 6. 推荐方案

### 6.1 开发/测试环境

使用本地部署或 PythonAnywhere 免费版。

### 6.2 生产环境

**推荐: PythonAnywhere 付费版**
- 完整支持 CBots 所有功能
- 提供 Always-On 任务确保 Bot 24/7 在线
- 适中的价格和良好的性能平衡

**替代方案: VPS (DigitalOcean, AWS EC2, Google Cloud)**
- 完全控制服务器
- 可以使用 Docker 和 systemd 服务确保 Bot 总是在线
- 可能需要更多配置和维护工作

## 7. 常见问题解答

### Q: 为什么不推荐 Vercel 或 Netlify 作为完整解决方案?
A: Vercel 和 Netlify 适合部署前端和无服务器函数，但不支持持续运行的后台进程，而 Telegram Bot 需要持续在线监听消息。

### Q: 免费版 PythonAnywhere 能运行 CBots 吗?
A: 可以运行，但有以下限制：
   - 没有 Always-On 任务，意味着 Bot 不能持续在线
   - CPU 使用时间限制
   - 网络访问限制

### Q: 如何处理 Telegram 身份验证?
A: 首次运行时，Telegram 会要求身份验证。在 PythonAnywhere 控制台运行 `main.py` 完成验证，之后可以在后台运行。

## 8. 联系支持

如果您在部署过程中遇到问题，请通过以下方式联系我们：
- GitHub Issues: [https://github.com/yourusername/CBots/issues](https://github.com/yourusername/CBots/issues)
- 邮箱: support@example.com 