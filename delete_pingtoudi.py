from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取MongoDB连接信息
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'trading_agents')

def delete_pingtoudi_data():
    """删除pingtoudi表中的所有数据"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db['pingtoudi']
        
        print(f"📋 连接到数据库: {DB_NAME}")
        print(f"📊 准备删除集合: pingtoudi 中的所有数据")
        
        # 获取删除前的记录数
        before_count = collection.count_documents({})
        print(f"\n🗑️ 删除前记录数: {before_count}")
        
        # 删除所有数据
        result = collection.delete_many({})
        
        # 获取删除后的记录数
        after_count = collection.count_documents({})
        
        print(f"✅ 删除成功")
        print(f"📊 删除的记录数: {result.deleted_count}")
        print(f"📊 删除后记录数: {after_count}")
        
        if after_count == 0:
            print("\n🎉 pingtoudi表中的所有数据已成功删除")
        else:
            print(f"\n⚠️ 表中仍有 {after_count} 条记录")
            
    except Exception as e:
        print(f"\n❌ 删除失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        client.close()

if __name__ == "__main__":
    delete_pingtoudi_data()