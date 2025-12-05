#!/usr/bin/env python3
"""
测试CSV导入API是否正常工作
"""

import csv
import json
import requests

# 配置
CSV_FILE_PATH = './2025_12_03_22_49_17.csv'
TEST_TABLE = 'test_api_pingtoudi'
API_URL = 'http://localhost:8000/api/csv'


def test_csv_import_api():
    """测试CSV导入API"""
    try:
        # 读取CSV文件
        data = []
        columns = []
        
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames
            for row in reader:
                # 处理空值
                cleaned_row = {k: v.strip() if v.strip() else None for k, v in row.items()}
                data.append(cleaned_row)
        
        print(f"✅ 成功读取CSV文件，共 {len(data)} 行数据")
        print(f"📋 列名: {columns}")
        
        # 测试数据验证API
        print("\n1️⃣ 测试数据验证API")
        print("-" * 30)
        validate_url = f"{API_URL}/validate"
        validate_payload = {
            "data": data[:5],  # 只测试前5行数据
            "columns": columns
        }
        
        validate_response = requests.post(validate_url, json=validate_payload)
        print(f"📡 验证API响应状态码: {validate_response.status_code}")
        print(f"📋 验证API响应: {validate_response.text}")
        
        if validate_response.status_code == 200:
            validate_result = validate_response.json()
            if validate_result.get('success'):
                print("✅ 数据验证成功")
            else:
                print(f"❌ 数据验证失败: {validate_result.get('message')}")
        else:
            print(f"❌ 数据验证API请求失败: {validate_response.text}")
        
        # 测试CSV导入API
        print("\n2️⃣ 测试CSV导入API")
        print("-" * 30)
        import_url = f"{API_URL}/import"
        import_payload = {
            "table": TEST_TABLE,
            "mode": "insert",
            "data": data[:10],  # 只导入前10行数据
            "columns": columns
        }
        
        import_response = requests.post(import_url, json=import_payload)
        print(f"📡 导入API响应状态码: {import_response.status_code}")
        print(f"📋 导入API响应: {import_response.text}")
        
        if import_response.status_code == 200:
            import_result = import_response.json()
            if import_result.get('success'):
                imported = import_result['data']['imported']
                failed = import_result['data']['failed']
                print(f"✅ 导入API成功，成功: {imported} 条，失败: {failed} 条")
                return True
            else:
                print(f"❌ 导入API失败: {import_result.get('message')}")
                return False
        else:
            print(f"❌ 导入API请求失败: {import_response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False


if __name__ == "__main__":
    print("🔍 开始测试CSV导入API")
    success = test_csv_import_api()
    
    if success:
        print("\n🎉 CSV导入API测试成功！")
    else:
        print("\n❌ CSV导入API测试失败！")
