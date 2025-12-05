from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取MongoDB连接信息
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'trading_agents')

def check_pingtoudi_table():
    """简单检查pingtoudi表的结构，确认是否包含导入日期字段"""
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db['pingtoudi']
        
        print(f"📋 连接到数据库: {DB_NAME}")
        print(f"📊 检查集合: pingtoudi")
        
        # 获取表中的第一条记录
        first_doc = collection.find_one()
        
        if first_doc:
            print("\n✅ 第一条记录内容：")
            print(f"字段列表：{list(first_doc.keys())}")
            print(f"\n详细内容：")
            for key, value in first_doc.items():
                print(f"  {key}: {value}")
            
            # 检查是否包含导入日期字段
            if '导入日期' in first_doc:
                print("\n✅ 表中包含 '导入日期' 字段")
            else:
                print("\n❌ 表中不包含 '导入日期' 字段")
        else:
            print("\n❌ 表为空")
            
        # 获取表的总记录数
        total_count = collection.count_documents({})
        print(f"\n📊 表中总记录数：{total_count}")
        
        # 检查是否有任何记录包含导入日期字段
        doc_with_date = collection.find_one({'导入日期': {'$exists': True}})
        if doc_with_date:
            print("\n✅ 表中至少有一条记录包含 '导入日期' 字段")
        else:
            print("\n❌ 表中没有任何记录包含 '导入日期' 字段")
            
    except Exception as e:
        print(f"\n❌ 检查失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        client.close()

if __name__ == "__main__":
    check_pingtoudi_table()