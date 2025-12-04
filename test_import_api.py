import requests
import jwt
from datetime import datetime, timedelta

# 生成JWT令牌
def generate_token(username: str, secret_key: str = "your-secret-key") -> str:
    """生成JWT令牌用于测试"""
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

# 测试导入数据的API
try:
    # 生成测试令牌
    token = generate_token("admin")
    print(f"Generated token: {token}")
    
    # 准备测试数据
    test_data = {
        "table": "test_table",
        "mode": "insert",
        "data": [
            {"name": "测试1", "value": "123"},
            {"name": "测试2", "value": "456"}
        ],
        "columns": ["name", "value"]
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post('http://localhost:8000/api/csv/import', json=test_data, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.text}")
    
    # 尝试解析JSON
    if response.status_code == 200:
        data = response.json()
        print(f"\nParsed JSON data:")
        print(f"Success: {data.get('success')}")
        print(f"Data: {data.get('data')}")
        print(f"Message: {data.get('message')}")
    else:
        print(f"\nError response:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()