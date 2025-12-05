#!/usr/bin/env python3
"""
测试CSV导入修复是否有效
"""

import csv
import json
import requests
from pymongo import MongoClient

# 配置
CSV_FILE_PATH = './2025_12_03_22_49_17.csv'
TEST_TABLE = 'test_pingtoudi'
MONGO_URI = 'mongodb://admin:tradingagents123@localhost:27017/'
MONGO_DB = 'tradingagents'
API_URL = 'http://localhost:8000/api/csv'


def read_csv_file():
    """读取CSV文件并转换为字典列表"""
    data = []
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 处理空值和特殊字符
                cleaned_row = {k: v.strip() if v.strip() else None for k, v in row.items()}
                data.append(cleaned_row)
        print(f"✅ 成功读取CSV文件，共 {len(data)} 行数据")
        return data
    except Exception as e:
        print(f"❌ 读取CSV文件失败: {e}")
        return []


def test_direct_mongo_import():
    """直接测试MongoDB插入功能"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[TEST_TABLE]
        
        # 读取CSV数据
        data = read_csv_file()
        if not data:
            return False
        
        # 清空测试表
        collection.delete_many({})
        print(f"✅ 已清空测试表 {TEST_TABLE}")
        
        # 插入数据
        result = collection.insert_many(data)
        print(f"✅ 直接MongoDB插入成功，共插入 {len(result.inserted_ids)} 条数据")
        
        # 验证数据
        count = collection.count_documents({})
        print(f"✅ 验证数据成功，表中共有 {count} 条数据")
        
        return count == len(data)
    except Exception as e:
        print(f"❌ 直接MongoDB插入失败: {e}")
        return False
    finally:
        # 关闭连接
        client.close()


def test_api_import():
    """测试API导入功能"""
    try:
        # 读取CSV数据
        data = read_csv_file()
        if not data:
            return False
        
        # 调用API导入数据
        import_url = f"{API_URL}/import"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "table": TEST_TABLE,
            "mode": "insert",
            "data": data,
            "columns": list(data[0].keys()) if data else []
        }
        
        print(f"🚀 调用API导入数据，URL: {import_url}")
        print(f"📋 导入数据量: {len(data)} 条")
        
        response = requests.post(import_url, headers=headers, data=json.dumps(payload))
        print(f"📡 API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 API响应结果: {result}")
            
            if result.get('success'):
                imported = result['data']['imported']
                failed = result['data']['failed']
                print(f"✅ API导入成功，成功: {imported} 条，失败: {failed} 条")
                return imported > 0
            else:
                print(f"❌ API导入失败: {result.get('message')}")
                return False
        else:
            print(f"❌ API请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API导入测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*50)
    print("🔍 测试CSV导入修复")
    print("="*50 + "\n")
    
    # 测试1: 直接MongoDB插入
    print("\n1️⃣ 测试直接MongoDB插入")
    print("-" * 30)
    mongo_success = test_direct_mongo_import()
    
    # 测试2: API导入
    print("\n2️⃣ 测试API导入")
    print("-" * 30)
    api_success = test_api_import()
    
    print("\n" + "="*50)
    print("📋 测试结果总结")
    print("="*50)
    print(f"✅ 直接MongoDB插入: {'成功' if mongo_success else '失败'}")
    print(f"✅ API导入: {'成功' if api_success else '失败'}")
    
    if mongo_success and api_success:
        print("\n🎉 所有测试通过！CSV导入修复成功！")
        return True
    else:
        print("\n❌ 测试失败！请检查修复是否正确。")
        return False


if __name__ == "__main__":
    main()
