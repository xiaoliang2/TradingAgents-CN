import requests

# 测试获取表列表的API
try:
    response = requests.get('http://localhost:8000/api/csv/tables')
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.text}")
    
    # 尝试解析JSON
    if response.status_code == 200:
        data = response.json()
        print(f"\nParsed JSON data:")
        print(f"Type: {type(data)}")
        print(f"Number of tables: {len(data)}")
        print(f"Tables: {data}")
    else:
        print(f"\nError response:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()