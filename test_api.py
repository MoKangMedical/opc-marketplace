#!/usr/bin/env python3
"""
OPC Marketplace 测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_api():
    """测试API基本功能"""
    print("🧪 开始测试 OPC Marketplace API...")
    print("=" * 50)
    
    # 1. 测试根端点
    print("1. 测试根端点...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 根端点正常: {data.get('message', '')}")
        else:
            print(f"   ✗ 根端点异常: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 连接失败: {e}")
        return
    
    # 2. 测试健康检查
    print("\n2. 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 健康检查正常: {data.get('status', '')}")
        else:
            print(f"   ✗ 健康检查异常: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 健康检查失败: {e}")
    
    # 3. 测试API信息
    print("\n3. 测试API信息...")
    try:
        response = requests.get(f"{API_URL}/info")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ API信息正常: {data.get('name', '')}")
            print(f"   ✓ 版本: {data.get('version', '')}")
            print(f"   ✓ 功能: {len(data.get('features', []))}个")
        else:
            print(f"   ✗ API信息异常: {response.status_code}")
    except Exception as e:
        print(f"   ✗ API信息失败: {e}")
    
    # 4. 测试用户注册
    print("\n4. 测试用户注册...")
    user_data = {
        "email": "test@example.com",
        "password": "Test123456",
        "full_name": "测试用户",
        "user_type": "CLIENT",
        "industry": "科技"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json=user_data)
        if response.status_code == 201:
            data = response.json()
            print(f"   ✓ 用户注册成功: {data.get('email', '')}")
            user_id = data.get('id')
        else:
            print(f"   ✗ 用户注册失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ✗ 用户注册异常: {e}")
    
    # 5. 测试用户登录
    print("\n5. 测试用户登录...")
    login_data = {
        "username": "test@example.com",
        "password": "Test123456"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            print(f"   ✓ 用户登录成功")
            print(f"   ✓ 访问令牌: {access_token[:20]}...")
            
            # 6. 测试需要认证的端点
            print("\n6. 测试需要认证的端点...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(f"{API_URL}/me", headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                print(f"   ✓ 获取用户信息成功: {user_info.get('full_name', '')}")
            else:
                print(f"   ✗ 获取用户信息失败: {response.status_code}")
        else:
            print(f"   ✗ 用户登录失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 用户登录异常: {e}")
    
    # 7. 测试技能列表
    print("\n7. 测试技能列表...")
    try:
        response = requests.get(f"{API_URL}/skills/")
        if response.status_code == 200:
            skills = response.json()
            print(f"   ✓ 技能列表正常: {len(skills)}个技能")
        else:
            print(f"   ✗ 技能列表异常: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 技能列表失败: {e}")
    
    # 8. 测试项目列表
    print("\n8. 测试项目列表...")
    try:
        response = requests.get(f"{API_URL}/projects/")
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            print(f"   ✓ 项目列表正常: {len(projects)}个项目")
        else:
            print(f"   ✗ 项目列表异常: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 项目列表失败: {e}")
    
    print("\n" + "=" * 50)
    print("✅ API测试完成！")
    print(f"📖 查看完整API文档: {BASE_URL}/docs")

if __name__ == "__main__":
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
    
    # 运行测试
    test_api()