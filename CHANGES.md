# CBots 变更日志

## 版本 0.23.29 (2024-07-22)
- 修复"Twitter client not initialized"错误
- 修改run-service-background.sh脚本，使用MODE=prd环境变量运行服务
- 修改web_routes.py中的Twitter初始化代码，确保Twitter核心服务在启动时正确初始化
- 修改twitter_api.py中的send_tweet方法，添加自动重试初始化Twitter客户端的功能
- 修改的文件：run-service-background.sh、web_routes.py、twitter_api.py
- 使用的是 Python 3.13，在这个版本中 imghdr 模块被移除了
- 我们通过创建 tweepy_patch.py 解决了这个问题，提供了一个替代实现

## 版本 0.23.28 (2024-07-22)
- 修复Twitter发送失败问题，错误为"Twitter service is not running"
- 修改TwitterAPI类的is_running属性初始化值为True
- 修改TwitterAPI.get_status()方法不再检查core.is_running属性
- 在main.py中输出Twitter服务状态，以便追踪服务状态
- 在main.py启动时和完成时输出Bot版本号
- 修改的文件：twitter_api.py、main.py

## 版本 0.23.27 (2024-07-22)
- 修复Twitter发送功能中的错误：'TwitterCore' object has no attribute 'is_running'
- 在TwitterCore类中添加is_running属性，并在start和stop方法中适当设置该属性
- 完善web_routes.py中发送推文的代码，正确传递image_url参数
- 修改的文件：twitter_core.py、web_routes.py

## 版本 0.23.26 (2024-07-22)
- 修复处理私有频道链接格式问题，去除前后空格
- 完善推特发送功能，添加对图片发送的支持
- 在推特页面添加图片URL输入功能
- 修改twitter_api.py，支持图片数据和图片URL参数
- 修改的文件：web_routes.py、twitter_api.py、templates/twitter.html

## 版本 0.23.25 (2024-07-22)
- 修改telegram.html页面的链接格式提示为英文
- 修复私有频道链接(https://t.me/c/1807106448/33)发送消息失败的问题
- 改进telegram_core.py中的get_group_entity方法，添加多种方式尝试获取私有频道实体
- 修复web_routes.py中Twitter发送消息时scheduled_time变量作用域问题
- 修改的文件：templates/telegram.html、web_routes.py、telegram_core.py

## 版本 0.23.24 (2024-07-22)
- 解决了数据库锁定问题，修改session文件存储方式
- 为每次启动创建新的session文件，使用时间戳命名
- 解决了"Error starting Telegram core service: database is locked"错误
- 创建sessions目录以存储会话文件
- 修改的文件：telegram_core.py

## 版本 0.23.23 (2024-07-22)
- 修复了私有频道链接格式 `https://t.me/c/1807106448/33` 发送消息失败的问题
- 在telegram_core.py中添加了对数字ID格式的处理
- 升级了telegram_core.py中的get_group_entity方法，支持数字频道ID
- 添加了flask-cors依赖到requirements.txt
- 创建static目录并复制favicon.ico到static目录解决404问题
- 修改了Flask应用创建，添加static_folder配置
- 修改的文件：telegram_core.py、telegram_api.py、requirements.txt、main.py

## 版本 0.23.22 (2024-07-22)
- 更新了web_routes.py中的版本号从0.23.21升级到0.23.22
- 添加了版本API接口：/api/version，供前端动态获取版本信息
- 修改了模板文件，使用JavaScript请求版本号，而不是服务器渲染
- 解决了服务启动后网页显示版本号不更新的问题
- 修改的文件：web_routes.py、templates/telegram.html、templates/twitter.html

## 版本 0.23.21 (2024-07-22)
- 更新了web_routes.py中的版本号从0.23.20升级到0.23.21
- 在web_routes.py中添加了根据MODE环境变量日志输出当前运行模式和端口
- 在main.py中添加了start_web_service函数，根据MODE环境变量选择不同的端口
- 修改.env文件，将MODE设置为prd，以便使用8872生产端口
- 修改的文件：web_routes.py、main.py、.env

## 版本 0.23.20 (2024-07-22)
- 增加了对不同Telegram链接格式的支持：
  - 社区名称/话题ID：`Account_Abstraction_Community/18472`
  - 私有频道链接：`https://t.me/c/1807106448/33`
  - 公开频道链接：`https://t.me/ETHPandaOrg/25`
- 更新了web_routes.py中的版本号从0.23.19升级到0.23.20
- 在telegram.html页面添加了明确的链接格式说明和示例
- 为run-service-background.sh和stop-service.sh脚本添加了执行权限
- 修改的文件：web_routes.py、templates/telegram.html 