import base64
import requests

BASE_URL = "http://127.0.0.1:8000"  # 按实际地址和端口修改


def test_connection():
    """测试服务是否可达（用 /docs 或任意路由探测）"""
    try:
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"[连接] /docs 状态码: {resp.status_code}")
        return resp.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[连接] 失败: {e}")
        return False


def test_screenshot():
    """测试截图接口，返回图片并保存到本地"""
    try:
        resp = requests.get(f"{BASE_URL}/screenshot", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            img_bytes = base64.b64decode(data["image_base64"])
            with open("test_screenshot.png", "wb") as f:
                f.write(img_bytes)
            print(f"[截图] 成功，已保存 test_screenshot.png，大小 {len(img_bytes)} 字节")
            return True
        else:
            print(f"[截图] 返回异常: {data}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[截图] 请求失败: {e}")
        return False


def test_execute():
    """测试动作执行接口，发一个简单的 click 动作示例"""
    payload = {"action": {"type": "click", "x": 100, "y": 100}}
    try:
        resp = requests.post(f"{BASE_URL}/execute", json=payload, timeout=10)
        print(f"[执行] 状态码: {resp.status_code}, 响应: {resp.text}")
        return resp.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[执行] 请求失败: {e}")
        return False


if __name__ == "__main__":
    print("=== 测试连接 ===")
    if not test_connection():
        print("服务不可达，后续测试跳过")
        exit(1)

    print("\n=== 测试截图 ===")
    test_screenshot()

    print("\n=== 测试执行动作 ===")
    test_execute()