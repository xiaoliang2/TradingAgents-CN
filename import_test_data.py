import asyncio
import os
from dotenv import load_dotenv
from app.services.database_service import DatabaseService

# 加载环境变量
load_dotenv()

# 测试数据
test_data = [
    {
        "序号": 1,
        "股票代码": "600519",
        "股票简称": "贵州茅台",
        "现价（元）": 1750.00,
        "涨跌幅（%）": 0.50
    },
    {
        "序号": 2,
        "股票代码": "000858",
        "股票简称": "五粮液",
        "现价（元）": 185.00,
        "涨跌幅（%）": -0.20
    },
    {
        "序号": 3,
        "股票代码": "000568",
        "股票简称": "泸州老窖",
        "现价（元）": 145.50,
        "涨跌幅（%）": 1.20
    },
    {
        "序号": 4,
        "股票代码": "600809",
        "股票简称": "山西汾酒",
        "现价（元）": 230.80,
        "涨跌幅（%）": 0.80
    },
    {
        "序号": 5,
        "股票代码": "002304",
        "股票简称": "洋河股份",
        "现价（元）": 128.30,
        "涨跌幅（%）": -0.30
    }
]

async def import_test_data():
    """导入测试数据到pingtoudi表，验证导入日期功能"""
    try:
        print("📋 准备导入测试数据到pingtoudi表")
        print(f"📊 测试数据量: {len(test_data)} 条")
        
        # 创建数据库服务实例
        db_service = DatabaseService()
        
        # 导入数据，使用insert模式
        result = await db_service.import_data(
            collection_name='pingtoudi',
            data=test_data,
            mode='insert'
        )
        
        print(f"\n✅ 数据导入结果:")
        print(f"   成功: {result['success_count']} 条")
        print(f"   失败: {result['error_count']} 条")
        
        if result['errors']:
            print("\n❌ 错误详情:")
            for error in result['errors']:
                print(f"   - {error}")
        else:
            print("\n🎉 所有数据导入成功")
            print("\n📝 说明:")
            print("   - 系统已自动为每条数据添加了'导入日期'字段")
            print("   - 您现在可以在数据筛选界面看到并使用导入日期筛选功能")
            print("   - 同一日期对同一表的更新会自动全量替换")
            
    except Exception as e:
        print(f"\n❌ 导入失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(import_test_data())