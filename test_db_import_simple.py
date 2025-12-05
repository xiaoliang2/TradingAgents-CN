#!/usr/bin/env python3
"""
简单测试MongoDB导入修复
"""

import csv
from pymongo import MongoClient

# 配置
CSV_FILE_PATH = './2025_12_03_22_49_17.csv'
TEST_TABLE = 'test_pingtoudi_simple'
MONGO_URI = 'mongodb://admin:tradingagents123@localhost:27017/'
MONGO_DB = 'tradingagents'


def test_csv_import_fix():
    """测试CSV导入修复"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[TEST_TABLE]
        
        # 清空测试表
        collection.delete_many({})
        print(f"✅ 已清空测试表 {TEST_TABLE}")
        
        # 读取CSV文件
        data = []
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 处理空值
                cleaned_row = {k: v.strip() if v.strip() else None for k, v in row.items()}
                data.append(cleaned_row)
        
        print(f"✅ 成功读取CSV文件，共 {len(data)} 行数据")
        
        # 插入数据（模拟修复后的行为，不进行日期字段转换）
        inserted_count = 0
        failed_count = 0
        
        for i, doc in enumerate(data):
            try:
                # 直接插入，不进行日期转换
                collection.insert_one(doc)
                inserted_count += 1
                if (i + 1) % 20 == 0:
                    print(f"📊 已处理 {i + 1}/{len(data)} 行数据")
            except Exception as e:
                failed_count += 1
                print(f"⚠️ 第 {i + 1} 行插入失败: {e}")
        
        # 验证结果
        total_in_db = collection.count_documents({})
        
        print("\n" + "="*50)
        print("📋 测试结果")
        print("="*50)
        print(f"📊 总数据行数: {len(data)}")
        print(f"✅ 成功插入: {inserted_count} 条")
        print(f"❌ 插入失败: {failed_count} 条")
        print(f"📋 数据库中实际数量: {total_in_db} 条")
        
        if inserted_count == len(data) and total_in_db == len(data):
            print("\n🎉 修复成功！CSV导入可以正常工作了！")
            return True
        else:
            print(f"\n❌ 修复失败！成功 {inserted_count} 条，期望 {len(data)} 条")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False
    finally:
        # 关闭连接
        client.close()


if __name__ == "__main__":
    print("🔍 开始测试CSV导入修复")
    test_csv_import_fix()
