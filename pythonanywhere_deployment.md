# PythonAnywhere 部署指南 - 精简版 MuteBot

本指南将帮助您在 PythonAnywhere 上部署精简版的 MuteBot 服务，该版本专注于自动禁言和密码验证功能。

## 前提条件

1. 拥有 PythonAnywhere 账号（免费账号即可）
2. 拥有 Telegram Bot Token (从 BotFather 获取)
3. 已获取 Telegram API ID 和 API Hash

## 步骤 1: 准备 Telegram API 凭证

确保您已经拥有以下信息：

- Telegram API ID
- Telegram API Hash
- Telegram Bot Token
- 目标群组用户名（如 @your_group_name）

## 步骤 2: 创建 PythonAnywhere 账号

1. 访问 [PythonAnywhere](https://www.pythonanywhere.com/) 并注册/登录账号
2. 登录后进入 Dashboard 页面

## 步骤 3: 创建新的 Web App

1. 在 Dashboard 中点击 "Web" 选项卡
2. 点击 "Add a new web app" 按钮
3. 选择 "Manual configuration"
4. 选择 Python 3.8 或更高版本
5. 设置路径为 `/bot`（或您喜欢的其他路径）

## 步骤 4: 获取代码

1. 在 Dashboard 中点击 "Consoles" 选项卡
2. 点击 "Bash" 创建一个新的 Bash 控制台
3. 执行以下命令克隆代码仓库：

```bash
cd ~
git clone https://github.com/your-username/mutebot.git
```

4. 进入项目目录：

```bash
cd mutebot
```

## 步骤 5: 配置环境变量

1. 在 Dashboard 中点击 "Files" 选项卡
2. 导航到 `/home/yourusername/mutebot/` 目录
3. 创建一个新文件 `.env`，内容如下：

```
TELEGRAM_API_ID=你的API_ID
TELEGRAM_API_HASH=你的API_HASH
TELEGRAM_BOT_TOKEN=你的BOT_TOKEN
TELEGRAM_GROUP=@你的群组名
MODE=prod
PRD_PORT=8872
```

## 步骤 6: 安装依赖

1. 回到 Bash 控制台
2. 创建并激活虚拟环境：

```bash
cd ~/mutebot
python -m venv venv
source venv/bin/activate && python main.py
```

3. 安装所需依赖：

```bash
pip install -r requirements.txt
```

## 步骤 7: 配置 WSGI 文件

1. 在 Dashboard 中点击 "Web" 选项卡
2. 点击 "WSGI configuration file" 链接编辑 WSGI 文件
3. 替换文件内容为：

```python
import sys
import os

# 添加项目路径
path = '/home/yourusername/mutebot'
if path not in sys.path:
    sys.path.append(path)

# 设置环境变量
os.environ['PYTHONPATH'] = path

# 导入补丁模块
try:
    import tweepy_patch
    print("已加载tweepy补丁，修复imghdr模块")
except Exception as e:
    print(f"加载tweepy补丁失败: {e}")

# 导入Flask应用
from web_service import app as application
```

4. 保存文件

## 步骤 8: 设置自动启动任务

1. 在 Dashboard 中点击 "Tasks" 选项卡
2. 在 "Schedule" 部分，添加以下命令作为定时任务：

```bash
cd ~/mutebot && source venv/bin/activate && python main.py >> bot.log 2>&1
```

3. 将任务设置为 "Daily"，选择当前时间（这样任务将立即运行，并每天在相同时间重启）

## 步骤 9: 启动服务

1. 在 Dashboard 中点击 "Web" 选项卡
2. 点击 "Reload" 按钮重新加载 Web 服务
3. 等待几分钟，让 MuteBot 服务完全启动

## 步骤 10: 验证部署

1. 访问您的 Web App URL (例如 `https://yourusername.pythonanywhere.com/bot`)
2. 您应该能看到 MuteBot 的服务状态页面
3. 在 Telegram 中，将您的机器人添加到目标群组并授予管理员权限
4. 测试以下功能：
   - 新用户加入时是否自动禁言
   - 用户是否可以通过私聊发送密码解除禁言
   - 群内是否可以使用 `/pass` 命令获取当日密码

## 故障排除

如果遇到问题，请检查以下内容：

1. 查看日志文件：
   ```bash
   cd ~/mutebot
   tail -f bot.log
   ```

2. 确保机器人有足够的权限：
   - 在 Telegram 群组中必须拥有管理员权限
   - 需要有禁言用户的权限

3. 检查会话文件是否正确：
   ```bash
   ls -la ~/mutebot/*.session
   ```
   如果没有 `.session` 文件，可能是首次登录失败

4. 重启服务：
   - 在 PythonAnywhere Tasks 页面手动运行任务
   - 重新加载 Web App（Web 选项卡中的 "Reload" 按钮）

## 保持服务运行

由于 PythonAnywhere 免费账户有使用限制，建议：

1. 每3个月登录一次您的账户以保持活跃
2. 设置额外的定时任务，每天ping一次您的Web服务以保持它的运行状态

---

祝您使用愉快！如有任何问题，请参考 [PythonAnywhere 帮助文档](https://help.pythonanywhere.com/) 或联系本项目维护者。 