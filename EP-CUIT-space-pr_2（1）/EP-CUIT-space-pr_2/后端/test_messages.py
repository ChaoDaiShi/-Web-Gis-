#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息通知系统测试脚本
用于验证后端API接口功能
"""

import requests
import json
import sys

# API基础URL
API_BASE = "http://127.0.0.1:5000/api"

def test_message_api():
    """测试消息通知系统API"""
    
    print("=" * 50)
    print("消息通知系统API测试")
    print("=" * 50)
    
    # 检查消息表是否存在
    print("\n0. 检查消息表是否存在...")
    try:
        response = requests.get(f"{API_BASE}/my/messages?user_id=1", timeout=5)
        if response.status_code == 500 and ("Table" in response.text or "doesn't exist" in response.text or "不存在" in response.text):
            print("✗ 消息表不存在，请先运行: python init_messages.py")
            return False
        print("✓ 消息表存在，继续测试...")
    except Exception as e:
        print(f"✗ 检查表存在性失败: {e}")
    
    # 测试用户ID（需要根据实际数据库中的用户ID调整）
    test_user_id = "1"  # 假设用户ID为1
    
    # 1. 测试发送系统消息
    print("\n1. 测试发送系统消息...")
    message_data = {
        "user_id": test_user_id,
        "title": "测试系统通知",
        "content": "这是一条测试系统消息，用于验证消息通知系统功能。",
        "message_type": "system"
    }
    
    try:
        response = requests.post(f"{API_BASE}/messages/send", 
                               json=message_data,
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 发送成功: {result.get('message')}")
        else:
            print(f"✗ 发送失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 发送请求异常: {e}")
    
    # 2. 测试获取用户消息列表
    print("\n2. 测试获取用户消息列表...")
    try:
        response = requests.get(f"{API_BASE}/my/messages?user_id={test_user_id}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                messages = result.get("data", [])
                print(f"✓ 获取成功: 共 {len(messages)} 条消息")
                for msg in messages[:3]:  # 显示前3条消息
                    print(f"   - {msg.get('title')} ({msg.get('message_type')})")
            else:
                print(f"✗ 获取失败: {result.get('message')}")
        else:
            print(f"✗ 获取失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 获取请求异常: {e}")
    
    # 3. 测试获取未读消息数量
    print("\n3. 测试获取未读消息数量...")
    try:
        response = requests.get(f"{API_BASE}/my/messages/unread-count?user_id={test_user_id}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                unread_count = result.get("unread_count", 0)
                print(f"✓ 未读消息数量: {unread_count}")
            else:
                print(f"✗ 获取失败: {result.get('message')}")
        else:
            print(f"✗ 获取失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 获取请求异常: {e}")
    
    # 4. 测试标记消息为已读（需要先获取一条消息的ID）
    print("\n4. 测试标记消息为已读...")
    try:
        # 先获取消息列表
        response = requests.get(f"{API_BASE}/my/messages?user_id={test_user_id}")
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("data"):
                first_message = result.get("data")[0]
                message_id = first_message.get("message_id")
                
                mark_data = {
                    "message_id": message_id,
                    "user_id": test_user_id
                }
                
                response = requests.post(f"{API_BASE}/my/messages/read", 
                                       json=mark_data,
                                       headers={"Content-Type": "application/json"})
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ 标记成功: {result.get('message')}")
                else:
                    print(f"✗ 标记失败: {response.status_code} - {response.text}")
            else:
                print("✗ 没有消息可标记")
        else:
            print(f"✗ 获取消息失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 标记请求异常: {e}")
    
    # 5. 测试删除消息
    print("\n5. 测试删除消息...")
    try:
        # 先获取消息列表
        response = requests.get(f"{API_BASE}/my/messages?user_id={test_user_id}")
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("data"):
                first_message = result.get("data")[0]
                message_id = first_message.get("message_id")
                
                delete_data = {
                    "message_id": message_id,
                    "user_id": test_user_id
                }
                
                response = requests.post(f"{API_BASE}/my/messages/delete", 
                                       json=delete_data,
                                       headers={"Content-Type": "application/json"})
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ 删除成功: {result.get('message')}")
                else:
                    print(f"✗ 删除失败: {response.status_code} - {response.text}")
            else:
                print("✗ 没有消息可删除")
        else:
            print(f"✗ 获取消息失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 删除请求异常: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    # 检查后端服务是否运行
    try:
        response = requests.get("http://127.0.0.1:5000/api/auth/test_db", timeout=5)
        if response.status_code == 200:
            print("后端服务运行正常，开始测试...")
            test_message_api()
        else:
            print("后端服务异常，请先启动后端服务")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("无法连接到后端服务，请确保后端服务正在运行")
        print("启动命令: python Start.py")
        sys.exit(1)
    except Exception as e:
        print(f"连接异常: {e}")
        sys.exit(1)