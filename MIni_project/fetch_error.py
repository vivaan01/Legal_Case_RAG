import urllib.request
import json

url = "http://localhost:8000/query_stream?query=What+did+the+Supreme+Court+rule+about+Ram+Mandir+ownership%3F&user_id=default_user"

try:
    with urllib.request.urlopen(url) as response:
        body = response.read().decode()
        print(json.loads(body))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(json.loads(body))
except Exception as e:
    print(f"Unexpected error: {str(e)}")