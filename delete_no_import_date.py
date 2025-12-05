from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取MongoDB连接信息
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://admin:tradingagents123@localhost:27017')
DB_NAME = os.getenv('MONGODB_DATABASE', os.getenv('MONGODB_DATABASE_NAME', 'tradingagents'))

def delete_no_import_date_data():
    """删除pingtoudi表中所有不含导入日期的数据"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db['pingtoudi']
        
        print(f"📋 连接到数据库: {DB_NAME}")
        print(f"📊 准备删除集合: pingtoudi 中所有不含导入日期的数据")
        
        # 获取删除前的记录数
        before_count = collection.count_documents({})
        print(f"\n🗑️ 删除前总记录数: {before_count}")
        
        # 统计不含导入日期字段的记录数
        no_date_count = collection.count_documents({'导入日期': {'$exists': False}})
        print(f"📊 不含导入日期的记录数: {no_date_count}")
        
        if no_date_count == 0:
            print("\n✅ 表中所有记录都已包含导入日期字段，无需删除")
            return
        
        # 用户已经明确要求删除，直接执行
        print(f"\n⚠️ 执行删除操作，删除 {no_date_count} 条不含导入日期的记录")
        
        # 执行删除操作
        result = collection.delete_many({'导入日期': {'$exists': False}})
        
        # 获取删除后的记录数
        after_count = collection.count_documents({})
        remaining_no_date = collection.count_documents({'导入日期': {'$exists': False}})
        
        print(f"\n✅ 删除成功")
        print(f"📊 删除的记录数: {result.deleted_count}")
        print(f"📊 删除前记录数: {before_count}")
        print(f"📊 删除后记录数: {after_count}")
        print(f"📊 剩余不含导入日期的记录数: {remaining_no_date}")
        
        # 验证删除结果
        if remaining_no_date == 0:
            print("\n🎉 所有不含导入日期的记录已成功删除")
            print(f"   表中剩余 {after_count} 条记录，都包含导入日期字段")
        else:
            print(f"\n⚠️ 仍有 {remaining_no_date} 条记录不含导入日期字段")
        
    except Exception as e:
        print(f"\n❌ 删除失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        client.close()

if __name__ == "__main__":
    delete_no_import_date_data()