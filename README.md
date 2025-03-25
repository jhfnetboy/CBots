# CBots
a bot for community operation and social media.

## Telegram bot
features:
- Create contents by AI and your contents feeding.
- Send messages to community group by bots.
- Web page interface

### Tech
- Telethon
- Docs：https://docs.telethon.dev/en/stable/basic/signing-in.html

### Design
我们要使用tlethon来完成一个web page 版本的telegram bot，
请参考@https://docs.telethon.dev/en/stable/basic/quick-start.html ，
来创建一个简单test示例，来确定appid和hash是否正常，请参考

这个产品0.1版本设计如下：
1. 用户获得自己的app id 和app hash：https://my.telegram.org
2. clone 本repo，运行
    ```
    
    uv python install 3.12
    uv venv --python 3.12
    source .venv/bin/activate

    pip3 install telethon

    python app.py
    ```
3. 自动访问localhost：8872
4. 显示页面，简单的输入文字和要求，经过AI加工，发送到指定telegram频道，可以定时
5. bot的自动回复，如果at bot，发送help，会给出一个内容链接列表和一些预定义的描述文字

### 0.1功能描述
主要功能：
Web界面可以发送消息到指定的Telegram频道或群组
支持定时发送消息
Bot会自动响应 /help 和 /content 命令
所有配置都通过环境变量管理，安全且灵活
这个实现满足了0.1版本的所有要求：
使用Telethon创建了Telegram bot
提供了Web界面
支持定时发送消息
实现了基本的bot命令响应
需要注意的是：
首次运行时，Telethon会要求用户进行身份验证
确保填写的频道和群组用户名是正确的
定时发送功能目前只支持每天固定时间发送，如果需要更复杂的定时功能，可以进一步扩展

### 0.11功能变更
1. 请在页面增加一个列出所有channel的功能，显示后选择某个channel，发送消息，可以设置时间发送
2. 请新增不同command（例如/help，/queryPNTS ，/hi等，配对不同的响应函数，函数根据发送内容，掉用内部函数或者外部api，完成内容加工后回复，不同command可以在env内配置，command1=queryPNTS，默认函数名就是command名，这样可以随时新增明亮和响应内容处理机制

### 0.12功能变更
新user进群会禁言4小时，和bot私聊每日密码才解禁
优化自动获取群的所有channel

### 0.20功能
新增twitter 网页（定时）发送功能
新增at twitter账号自动回复功能（固定内容）

已实现：
Web界面功能：
访问 http://localhost:8872 可以看到完整的控制面板
显示可用频道列表
可以选择频道并发送消息
支持定时发送
动态命令系统：
所有命令都在 config.py 中配置
每个命令都有对应的处理函数
可以轻松添加新命令
帮助消息自动更新
新增的命令：
/help - 显示帮助信息
/content - 显示内容列表
/queryPNTS - 查询 PNTS 信息（待实现具体逻辑）
/hi - 打招呼

### 如何初始化配置

#### 获取 API ID 和 API Hash：
访问 https://my.telegram.org
使用你的手机号码登录
点击 "API development tools"
创建一个新的应用（填写应用名称和简短描述）
创建后，你会看到 api_id 和 api_hash
将这两个值填入 .env 文件：


#### 获取 Channel 和 Group 用户名：
对于频道（Channel）：
打开你的 Telegram 频道
点击频道名称
在频道信息中，你会看到类似 @channelname 的格式
这就是你的 TELEGRAM_CHANNEL 值
对于群组（Group）：
打开你的 Telegram 群组
点击群组名称
在群组信息中，你会看到类似 @groupname 的格式
这就是你的 TELEGRAM_GROUP 值
#### 获取 Bot 用户名
如果你还没有创建 bot：
在 Telegram 中找到 @BotFather
发送 /newbot 命令
按照提示设置 bot 名称和用户名
BotFather 会给你一个 bot token
记录下 bot 的用户名（以 @ 开头）
将 bot 用户名填入 .env 文件：
Apply to README.md
你的bot用户名
完整的 .env 文件示例：
Apply to README.md
configuration
#### 注意事项
确保你的 bot 已经被添加到目标频道和群组中
bot 需要有发送消息的权限
频道和群组的用户名必须包含 @ 符号
所有值都不要加引号，直接填写即可
需要我详细解释某个部分吗？或者需要帮助创建 bot？

## Twitter bot
获取 Twitter API 配置，你需要：
访问 Twitter 开发者平台：https://developer.twitter.com/
创建一个开发者账号（如果还没有的话）
创建一个项目和应用
获取以下凭证：
API Key (Consumer Key)
API Secret (Consumer Secret)
Access Token
Access Token Secret
Bearer Token
然后在你的 .env 文件中添加这些配置：

Found group: AAStar Community (ID: 1866085490)

## 代码结构
文件关系：
run.py (入口文件)
  ├── app.py (Flask应用)
  │     └── bot_manager.py (机器人管理器)
  │           ├── bot.py (Telegram机器人)
  │           └── twitter_bot.py (Twitter机器人)
  └── command_manager.py (命令管理器)

功能逻辑：
run.py: 启动应用，初始化机器人管理器和Flask服务器
app.py: Flask应用，处理Web请求
bot_manager.py: 管理所有机器人的生命周期
bot.py: Telegram机器人的具体实现
twitter_bot.py: Twitter机器人的具体实现
command_manager.py: 统一管理所有机器人的命令和消息处理