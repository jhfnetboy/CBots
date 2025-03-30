#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

# 检查目录结构
def check_directories():
    directories = [
        "public",
        "netlify/functions-build",
        "netlify/functions-build/flask_app",
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            print(f"❌ 目录 {directory} 不存在")
            return False
        print(f"✅ 目录 {directory} 存在")
    
    return True

# 检查关键文件
def check_files():
    files = [
        "public/index.html",
        "netlify/functions-build/hello.js",
        "netlify/functions-build/flask_app/requirements.txt",
        "netlify/functions-build/flask_app/__init__.py",
        "netlify/functions-build/flask_app/app.py",
        "netlify.toml",
    ]
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ 文件 {file_path} 不存在")
            return False
        print(f"✅ 文件 {file_path} 存在")
    
    return True

# 检查 netlify.toml 配置
def check_netlify_config():
    toml_path = Path("netlify.toml")
    
    if not toml_path.exists():
        print("❌ netlify.toml 不存在")
        return False
    
    with open(toml_path, "r") as f:
        content = f.read()
    
    checks = [
        ("build.command", "pip install -r requirements.txt && bash netlify_deploy.sh" in content),
        ("build.publish", "publish = \"public\"" in content),
        ("build.functions", "functions = \"netlify/functions-build\"" in content),
        ("redirects", "[[redirects]]" in content),
    ]
    
    all_passed = True
    for check_name, result in checks:
        if result:
            print(f"✅ netlify.toml: {check_name} 配置正确")
        else:
            print(f"❌ netlify.toml: {check_name} 配置有问题")
            all_passed = False
    
    return all_passed

# 主函数
def main():
    print("=== 检查部署配置 ===\n")
    
    directories_ok = check_directories()
    files_ok = check_files()
    config_ok = check_netlify_config()
    
    print("\n=== 检查结果 ===")
    if directories_ok and files_ok and config_ok:
        print("✅ 所有检查通过，配置看起来正确")
        print("👉 可以运行 'netlify deploy --prod' 来部署")
    else:
        print("❌ 部分检查未通过，请查看上面的详细信息")

if __name__ == "__main__":
    main() 