from urllib.parse import unquote

# 假设这是从请求中获取的原始参数
raw_color = "é»\x91è\x89²"

# 使用unquote进行解码
decoded_color = unquote(raw_color)

print(f"Decoded color: {decoded_color}")