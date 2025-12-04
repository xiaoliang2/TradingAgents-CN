from app.services.user_service import user_service
import asyncio

async def check_admin():
    # 创建默认管理员用户
    admin = await user_service.create_admin_user()
    print(f"管理员用户: {admin.username if admin else '不存在'}")
    
    # 列出所有用户
    users = await user_service.list_users()
    print(f"用户列表: {[user.username for user in users]}")

if __name__ == "__main__":
    asyncio.run(check_admin())