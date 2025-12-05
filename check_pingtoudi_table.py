import asyncio
from app.services.database_service import get_mongo_db

async def check_pingtoudi_table():
    """检查pingtoudi表的结构，确认是否包含导入日期字段"""
    try:
        db = await get_mongo_db()
        collection = db['pingtoudi']
        
        # 获取表中的第一条记录
        first_doc = await collection.find_one()
        
        if first_doc:
            print("📋 pingtoudi表的字段结构：")
            print(f"字段列表：{list(first_doc.keys())}")
            print(f"\n第一条记录内容：")
            for key, value in first_doc.items():
                print(f"  {key}: {value}")
            
            # 检查是否包含导入日期字段
            if '导入日期' in first_doc:
                print("\n✅ 表中包含 '导入日期' 字段")
            else:
                print("\n❌ 表中不包含 '导入日期' 字段")
        else:
            print("❌ pingtoudi表为空")
            
        # 获取表的总记录数
        total_count = await collection.count_documents({})
        print(f"\n📊 表中总记录数：{total_count}")
        
    except Exception as e:
        print(f"❌ 检查失败：{e}")

if __name__ == "__main__":
    asyncio.run(check_pingtoudi_table())