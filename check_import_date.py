from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取MongoDB连接信息
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://admin:tradingagents123@localhost:27017')
DB_NAME = os.getenv('MONGODB_DATABASE', os.getenv('MONGODB_DATABASE_NAME', 'tradingagents'))

def check_import_date_field():
    """检查pingtoudi表中的数据是否包含导入日期字段"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db['pingtoudi']
        
        print(f"📋 连接到数据库: {DB_NAME}")
        print(f"📊 检查集合: pingtoudi")
        
        # 获取记录数
        total_count = collection.count_documents({})
        print(f"\n📊 表中的记录数: {total_count}")
        
        # 检查前10条记录是否包含导入日期字段
        print("\n📝 检查前10条记录是否包含导入日期字段:")
        cursor = collection.find().limit(10)
        
        has_import_date = False
        records_with_date = 0
        
        for i, doc in enumerate(cursor, 1):
            print(f"\n记录 {i}:")
            print(f"  字段列表: {list(doc.keys())}")
            
            if '导入日期' in doc:
                print(f"  ✅ 包含导入日期字段: {doc['导入日期']}")
                has_import_date = True
                records_with_date += 1
            else:
                print("  ❌ 不包含导入日期字段")
        
        print(f"\n📊 检查结果:")
        print(f"   - 检查了 {min(10, total_count)} 条记录")
        print(f"   - 其中 {records_with_date} 条包含导入日期字段")
        
        # 统计包含导入日期字段的记录数
        records_with_import_date = collection.count_documents({'导入日期': {'$exists': True}})
        print(f"   - 表中共有 {records_with_import_date} 条记录包含导入日期字段")
        print(f"   - 占总记录数的 {records_with_import_date/total_count*100:.2f}%")
        
        # 检查记录中是否有其他日期相关字段
        print("\n📝 检查记录中的其他日期相关字段:")
        cursor = collection.find().limit(1)
        first_doc = next(cursor, None)
        if first_doc:
            print("   - 所有字段:")
            for key in first_doc.keys():
                print(f"     {key}")
        
        print(f"\n🎉 数据库连接和查询成功")
        
    except Exception as e:
        print(f"\n❌ 查询失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        client.close()

if __name__ == "__main__":
    check_import_date_field()