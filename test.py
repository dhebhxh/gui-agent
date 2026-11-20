from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

print("正在测试纯文本...")
response = client.chat.completions.create(
    model="qwen-vl",
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7,
    max_tokens=100
)
print("文本回复:", response.choices[0].message.content)

print("\n正在测试图片...")
response_img = client.chat.completions.create(
    model="qwen-vl",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "图片里有什么？"},
                {
                    "type": "image_url",
                    # 用官方测试图，确保图片链接有效
                    "image_url": {"url": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"}
                }
            ]
        }
    ],
    temperature=0.7,
    max_tokens=200
)
print("图片回复:", response_img.choices[0].message.content)