from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic(base_url="https://api.deepseek.com/anthropic")
model = "deepseek-v4-flash"
system = "你是一个 ACME 购物助手。"

message = client.messages.create(
    model=model,
    system=system,
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "你好"
        }
    ]
)

for block in message.content:
    # print(block)
    if block.type == "text":
        print(block.text)