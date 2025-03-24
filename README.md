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
    pip3 install telethon
    python start.py
    ```
3. 自动访问localhost：8872
4. 显示页面，简单的输入文字和要求，经过AI加工，发送到指定telegram频道，可以定时
5. bot的自动回复，如果at bot，发送help，会给出一个内容链接列表和一些预定义的描述文字



## Twitter bot
TODO