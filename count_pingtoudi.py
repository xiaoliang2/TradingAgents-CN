from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取MongoDB连接信息
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://admin:tradingagents123@localhost:27017')
DB_NAME = os.getenv('MONGODB_DATABASE', os.getenv('MONGODB_DATABASE_NAME', 'tradingagents'))

def count_pingtoudi_data():
    """查询pingtoudi表中的记录数"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db['pingtoudi']
        
        print(f"📋 连接到数据库: {DB_NAME}")
        print(f"📊 查询集合: pingtoudi")
        
        # 获取记录数
        total_count = collection.count_documents({})
        
        print(f"\n✅ 查询结果:")
        print(f"📊 pingtoudi表中的记录数: {total_count}")
        
        if total_count == 0:
            print("\n⚠️ 表中没有数据")
        else:
            print(f"\n🎉 表中有 {total_count} 条数据")
            
            # 显示前3条记录的基本信息
            print("\n📝 前3条记录示例:")
            cursor = collection.find().limit(3)
            for i, doc in enumerate(cursor, 1):
                print(f"\n记录 {i}:")
                for key, value in doc.items():
                    if key != '_id':  # 不显示_id字段
                        print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"\n❌ 查询失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        client.close()

if __name__ == "__main__":
    count_pingtoudi_data()