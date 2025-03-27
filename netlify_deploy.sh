#!/bin/bash

# 设置 Python 版本
export PYTHON_VERSION=3.11
export PYTHON_BIN=python3.11
export PIP_BIN=pip3.11

VERSION=$(cat version.txt)

# 确保public目录存在
mkdir -p public

# 复制模板文件
cp -r templates/* public/ 2>/dev/null || echo "No templates to copy"
cp -r static/* public/ 2>/dev/null || echo "No static files to copy"

# 确保index.html存在
if [ ! -f "public/index.html" ]; then
  echo "Creating default index.html"
  cat > public/index.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>CBots</title>
    <meta http-equiv="refresh" content="0;url=/telegram">
</head>
<body>
    <p>Redirecting to Telegram page...</p>
</body>
</html>
EOL
fi

# 准备函数目录
mkdir -p netlify/functions-build

# 复制JS函数
cp netlify/functions/*.js netlify/functions-build/ 2>/dev/null || echo "No JS functions to copy"

# 复制Python函数
cp netlify/functions/*.py netlify/functions-build/ 2>/dev/null || echo "No Python functions to copy"

# 确保requirements.txt被复制到函数目录
cp requirements.txt netlify/functions-build/ 2>/dev/null || echo "No requirements.txt found"

# 创建单独的flask_app函数包
mkdir -p netlify/functions-build/flask_app
cat > netlify/functions-build/flask_app/requirements.txt << EOL
flask==3.0.2
telethon==1.39.0
tweepy==4.15.0
python-dotenv==1.0.1
EOL

cat > netlify/functions-build/flask_app/__init__.py << EOL
# This file makes the directory a Python package
EOL

# 复制主Flask应用代码
mkdir -p netlify/functions-build/flask_app/app
cp -r app.py netlify/functions-build/flask_app/
cp -r bot_manager.py netlify/functions-build/flask_app/ 2>/dev/null || echo "No bot_manager.py found"
cp -r telegram_bot.py netlify/functions-build/flask_app/ 2>/dev/null || echo "No telegram_bot.py found"
cp -r twitter_bot.py netlify/functions-build/flask_app/ 2>/dev/null || echo "No twitter_bot.py found"
cp -r command_manager.py netlify/functions-build/flask_app/ 2>/dev/null || echo "No command_manager.py found"

# 部署到Netlify
echo "Ready for deployment. Run:"
echo "netlify deploy --prod" 