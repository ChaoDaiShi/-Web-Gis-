#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录注册功能测试脚本
用于检测登录注册功能可能出现的问题
"""

import sys
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.error("未安装 requests 库，请先安装: pip install requests")
    sys.exit(1)

BASE_URL = "http://127.0.0.1:5000"

def test_register():
    """测试注册功能"""
    logger.info("=" * 60)
    logger.info("【测试注册功能】")
    logger.info("=" * 60)
    
    test_cases = [
        {
            "name": "正常注册",
            "data": {
                "username": f"test_user_{int(datetime.now().timestamp())}",
                "email": f"test_{int(datetime.now().timestamp())}@example.com",
                "password": "123456"
            },
            "expected_status": 201,
            "expected_message": "User created successfully"
        },
        {
            "name": "缺少用户名",
            "data": {
                "email": "missing_username@example.com",
                "password": "123456"
            },
            "expected_status": 400,
            "expected_message": "Missing required fields"
        },
        {
            "name": "缺少密码",
            "data": {
                "username": "missing_password_user",
                "email": "missing_password@example.com"
            },
            "expected_status": 400,
            "expected_message": "Missing required fields"
        },
        {
            "name": "空数据",
            "data": {},
            "expected_status": 400,
            "expected_message": "No input data provided"
        },
        {
            "name": "用户名已存在",
            "data": {
                "username": "duplicate_user",
                "email": "unique_email@example.com",
                "password": "123456"
            },
            "expected_status": 400,
            "expected_message": "Username already exists"
        }
    ]
    
    # 先创建一个用于测试重复用户名的用户
    duplicate_user_data = {
        "username": "duplicate_user",
        "email": "duplicate_user@example.com",
        "password": "123456"
    }
    try:
        requests.post(f"{BASE_URL}/api/auth/register", json=duplicate_user_data)
    except Exception as e:
        logger.warning(f"预创建测试用户失败: {e}")
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        logger.info(f"\n【测试用例 {i}】{case['name']}")
        logger.debug(f"请求数据: {case['data']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/register",
                json=case['data'],
                timeout=5
            )
            
            logger.debug(f"响应状态码: {response.status_code}")
            try:
                response_data = response.json()
                logger.debug(f"响应数据: {response_data}")
            except:
                response_data = {"message": response.text}
            
            if response.status_code == case['expected_status']:
                if case['expected_message'] in response_data.get('message', ''):
                    logger.info(f"[PASS] {case['name']}")
                    passed += 1
                else:
                    logger.error(f"[FAIL] {case['name']}")
                    logger.error(f"  期望消息: {case['expected_message']}")
                    logger.error(f"  实际消息: {response_data.get('message')}")
                    failed += 1
            else:
                logger.error(f"[FAIL] {case['name']}")
                logger.error(f"  期望状态码: {case['expected_status']}")
                logger.error(f"  实际状态码: {response.status_code}")
                failed += 1
                
        except requests.exceptions.ConnectionError:
            logger.error(f"[FAIL] {case['name']}")
            logger.error("  错误: 无法连接到后端服务器")
            logger.error("  请确保后端服务已启动: python Start.py")
            failed += 1
        except requests.exceptions.Timeout:
            logger.error(f"[FAIL] {case['name']}")
            logger.error("  错误: 请求超时")
            failed += 1
        except Exception as e:
            logger.error(f"[FAIL] {case['name']}")
            logger.error(f"  错误: {str(e)}")
            failed += 1
    
    logger.info(f"\n【注册测试结果】通过: {passed}/{len(test_cases)}, 失败: {failed}/{len(test_cases)}")
    return passed, failed

def test_login():
    """测试登录功能"""
    logger.info("\n" + "=" * 60)
    logger.info("【测试登录功能】")
    logger.info("=" * 60)
    
    # 先创建一个测试用户
    test_user = {
        "username": f"login_test_{int(datetime.now().timestamp())}",
        "email": f"login_test_{int(datetime.now().timestamp())}@example.com",
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user, timeout=5)
        if response.status_code == 201:
            logger.info(f"已创建测试用户: {test_user['email']}")
        else:
            logger.warning(f"创建测试用户失败，可能已存在")
    except Exception as e:
        logger.error(f"创建测试用户失败: {e}")
        return 0, 6
    
    test_cases = [
        {
            "name": "正常登录",
            "data": {
                "email": test_user["email"],
                "password": "123456"
            },
            "expected_status": 200,
            "expected_message": "Login successful"
        },
        {
            "name": "密码错误",
            "data": {
                "email": test_user["email"],
                "password": "wrong_password"
            },
            "expected_status": 401,
            "expected_message": "Invalid email or password"
        },
        {
            "name": "用户不存在",
            "data": {
                "email": "not_exist@example.com",
                "password": "123456"
            },
            "expected_status": 401,
            "expected_message": "Invalid email or password"
        },
        {
            "name": "缺少邮箱",
            "data": {
                "password": "123456"
            },
            "expected_status": 400,
            "expected_message": "Missing required fields"
        },
        {
            "name": "缺少密码",
            "data": {
                "email": test_user["email"]
            },
            "expected_status": 400,
            "expected_message": "Missing required fields"
        },
        {
            "name": "空数据",
            "data": {},
            "expected_status": 400,
            "expected_message": "No input data provided"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        logger.info(f"\n【测试用例 {i}】{case['name']}")
        logger.debug(f"请求数据: {case['data']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json=case['data'],
                timeout=5
            )
            
            logger.debug(f"响应状态码: {response.status_code}")
            try:
                response_data = response.json()
                logger.debug(f"响应数据: {response_data}")
            except:
                response_data = {"message": response.text}
            
            if response.status_code == case['expected_status']:
                if case['expected_message'] in response_data.get('message', ''):
                    logger.info(f"[PASS] {case['name']}")
                    passed += 1
                else:
                    logger.error(f"[FAIL] {case['name']}")
                    logger.error(f"  期望消息: {case['expected_message']}")
                    logger.error(f"  实际消息: {response_data.get('message')}")
                    failed += 1
            else:
                logger.error(f"[FAIL] {case['name']}")
                logger.error(f"  期望状态码: {case['expected_status']}")
                logger.error(f"  实际状态码: {response.status_code}")
                failed += 1
                
        except requests.exceptions.ConnectionError:
            logger.error(f"[FAIL] {case['name']}")
            logger.error("  错误: 无法连接到后端服务器")
            failed += 1
        except requests.exceptions.Timeout:
            logger.error(f"[FAIL] {case['name']}")
            logger.error("  错误: 请求超时")
            failed += 1
        except Exception as e:
            logger.error(f"[FAIL] {case['name']}")
            logger.error(f"  错误: {str(e)}")
            failed += 1
    
    logger.info(f"\n【登录测试结果】通过: {passed}/{len(test_cases)}, 失败: {failed}/{len(test_cases)}")
    return passed, failed

def test_database_connection():
    """测试数据库连接"""
    logger.info("\n" + "=" * 60)
    logger.info("【测试数据库连接】")
    logger.info("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/test_db", timeout=5)
        logger.debug(f"响应状态码: {response.status_code}")
        
        try:
            response_data = response.json()
            logger.debug(f"响应数据: {response_data}")
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                logger.info(f"[PASS] 数据库连接正常")
                logger.info(f"  用户数量: {response_data.get('count', 0)}")
                return True
            else:
                logger.error(f"[FAIL] 数据库连接失败")
                logger.error(f"  错误信息: {response_data.get('message')}")
                return False
        except:
            logger.error(f"[FAIL] 数据库响应解析失败")
            logger.error(f"  响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("[FAIL] 无法连接到后端服务器")
        return False
    except requests.exceptions.Timeout:
        logger.error("[FAIL] 请求超时")
        return False
    except Exception as e:
        logger.error(f"[FAIL] 数据库测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("\n" + "=" * 60)
    logger.info("登录注册功能测试脚本")
    logger.info("=" * 60)
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"后端服务地址: {BASE_URL}")
    logger.info("=" * 60)
    
    # 测试数据库连接
    db_ok = test_database_connection()
    
    if not db_ok:
        logger.error("\n数据库连接失败，跳过登录注册测试")
        logger.error("请先确保:")
        logger.error("1. MySQL服务已启动")
        logger.error("2. 数据库配置正确")
        logger.error("3. 后端服务已运行: python Start.py")
        return
    
    # 测试注册功能
    reg_passed, reg_failed = test_register()
    
    # 测试登录功能
    login_passed, login_failed = test_login()
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    total_passed = reg_passed + login_passed
    total_failed = reg_failed + login_failed
    total_tests = total_passed + total_failed
    
    logger.info(f"注册测试: 通过 {reg_passed} / 失败 {reg_failed}")
    logger.info(f"登录测试: 通过 {login_passed} / 失败 {login_failed}")
    logger.info(f"总测试: 通过 {total_passed} / 失败 {total_failed} ({total_tests} 个用例)")
    
    if total_failed == 0:
        logger.info("\n[SUCCESS] 所有测试通过!")
    else:
        logger.error(f"\n[FAILURE] 有 {total_failed} 个测试用例失败，请检查错误信息")

if __name__ == "__main__":
    main()