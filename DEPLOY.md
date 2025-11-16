# 部署指南

## 部署到 Netlify

1. 安装 Netlify CLI
```bash
npm install -g netlify-cli
```

2. 登录 Netlify
```bash
netlify login
```

3. 初始化项目
```bash
netlify init
```

4. 部署
```bash
netlify deploy --prod
```

## 部署到 Vercel

1. 安装 Vercel CLI
```bash
npm install -g vercel
```

2. 登录 Vercel
```bash
vercel login
```

3. 部署
```bash
vercel
```

## 环境变量配置

在 Netlify/Vercel 仪表板中设置以下环境变量：

```env
# Telegram 配置
TELEGRAM_API_ID=你的API_ID
TELEGRAM_API_HASH=你的API_HASH
TELEGRAM_BOT_TOKEN=你的BOT_TOKEN
TELEGRAM_CHANNEL=@你的频道名
TELEGRAM_GROUP=@你的群组名
```

## 社区使用指南

### 方案一：自托管

1. 克隆仓库
```bash
git clone https://github.com/yourusername/CBots.git
cd CBots
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

5. 运行
```bash
python main.py
```

### 方案二：使用我们的托管服务

1. 访问我们的部署页面：https://cbots.yourdomain.com

2. 点击 "Add Bot" 按钮

3. 输入你的 Bot Token（从 @BotFather 获取）

4. 选择要添加的群组

5. 点击 "Install" 完成安装

### 方案三：使用 Docker

1. 拉取镜像
```bash
docker pull yourusername/cbots:latest
```

2. 运行容器
```bash
docker run -d \
  -e TELEGRAM_API_ID=你的API_ID \
  -e TELEGRAM_API_HASH=你的API_HASH \
  -e TELEGRAM_BOT_TOKEN=你的BOT_TOKEN \
  -e TELEGRAM_GROUP=@你的群组名 \
  yourusername/cbots:latest
```

## 注意事项

1. 确保你的 bot 已经被添加到目标频道和群组中
2. bot 需要有管理员权限
3. 频道和群组的用户名必须包含 @ 符号
4. 所有值都不要加引号，直接填写即可

## 常见问题

1. 如果遇到权限问题，请确保 bot 是群组管理员
2. 如果消息发送失败，检查频道/群组用户名是否正确
3. 如果 bot 没有响应，检查 bot token 是否正确

## 更新日志

### v0.23.2
- 修复了新用户禁言功能
- 改进了每日密码系统
- 优化了消息处理逻辑
- 添加了版本号显示 