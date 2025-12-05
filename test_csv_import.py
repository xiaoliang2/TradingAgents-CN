#!/usr/bin/env python3
"""
测试CSV文件导入脚本
用于诊断为什么CSV文件导入失败
"""

import os
import sys
import csv
import json
from pymongo import MongoClient

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置
MONGO_URI = "mongodb://admin:tradingagents123@localhost:27017/"
DATABASE_NAME = "tradingagents"
COLLECTION_NAME = "pingtoudi_test"
CSV_FILE = "2025_12_03_22_49_17.csv"

print("=" * 60)
print("CSV导入测试脚本")
print("=" * 60)

# 1. 连接数据库
try:
    print(f"1. 连接数据库: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    print(f"   ✅ 成功连接到数据库: {DATABASE_NAME}")
    print(f"   ✅ 成功获取集合: {COLLECTION_NAME}")
    
    # 清除测试集合
    collection.delete_many({})
    print(f"   ✅ 已清除测试集合中的现有数据")
except Exception as e:
    print(f"   ❌ 连接数据库失败: {e}")
    sys.exit(1)

# 2. 读取CSV文件
try:
    print(f"\n2. 读取CSV文件: {CSV_FILE}")
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    print(f"   ✅ 成功读取CSV文件")
    print(f"   ✅ 共 {len(csv_data)} 行数据")
    print(f"   ✅ 字段名: {list(csv_data[0].keys()) if csv_data else []}")
    print(f"   ✅ 第一条数据: {json.dumps(csv_data[0], ensure_ascii=False) if csv_data else '无'}")
except Exception as e:
    print(f"   ❌ 读取CSV文件失败: {e}")
    sys.exit(1)

# 3. 尝试导入数据
try:
    print(f"\n3. 尝试导入数据到集合: {COLLECTION_NAME}")
    
    # 逐个插入数据，捕获每个文档的错误
    success_count = 0
    error_count = 0
    errors = []
    
    for i, doc in enumerate(csv_data):
        try:
            collection.insert_one(doc)
            success_count += 1
            if i < 5 or i == len(csv_data) - 1:
                print(f"   ✅ 导入第 {i+1} 条数据成功")
        except Exception as e:
            error_count += 1
            errors.append({
                "row": i+1,
                "error": str(e),
                "data": doc
            })
            if i < 5 or i == len(csv_data) - 1:
                print(f"   ❌ 导入第 {i+1} 条数据失败: {e}")
    
    print(f"\n4. 导入结果:")
    print(f"   ✅ 成功导入: {success_count} 条")
    print(f"   ❌ 导入失败: {error_count} 条")
    
    if errors:
        print(f"\n5. 错误详情 (显示前5个错误):")
        for i, error in enumerate(errors[:5]):
            print(f"   {i+1}. 第 {error['row']} 行: {error['error']}")
            print(f"      数据: {json.dumps(error['data'], ensure_ascii=False)}")
            print()
    
    # 验证导入结果
    print(f"\n6. 验证导入结果:")
    total_docs = collection.count_documents({})
    print(f"   ✅ 集合中的文档总数: {total_docs}")
    
    if total_docs > 0:
        sample_docs = list(collection.find({}).limit(2))
        print(f"   ✅ 采样文档:")
        for doc in sample_docs:
            doc.pop('_id')
            print(f"      {json.dumps(doc, ensure_ascii=False)}")
    
    # 清理测试集合
    collection.delete_many({})
    print(f"   ✅ 已清理测试集合")
    
except Exception as e:
    print(f"   ❌ 导入数据失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)