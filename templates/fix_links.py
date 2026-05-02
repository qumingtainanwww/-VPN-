import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换GitHub链接（纯文本格式）
old_github = r'<div class="link-line" style="margin-top:10px;"><a href="https://github.com/qumingtianwww/NodeCollector" target="_blank" style="color:#888;text-decoration:none;">GitHub：https://github.com/qumingtianwww/NodeCollector</a></div>'
new_github = '<div class="link-line">GitHub：https://github.com/qumingtianwww/NodeCollector</div>'
content = content.replace(old_github, new_github)

# 替换爱发电链接（纯文本格式）
old_afdian = r'<div class="link-line" style="margin-top:8px;"><a href="https://afdian.net/a/shasha-vault" target="_blank" style="color:#888;text-decoration:none;">爱发电：https://afdian.net/a/shasha-vault</a></div>'
new_afdian = '<div class="link-line">爱发电：https://afdian.net/a/shasha-vault</div>'
content = content.replace(old_afdian, new_afdian)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已成功替换链接为纯文本格式！")
print("GitHub：https://github.com/qumingtianwww/NodeCollector")
print("爱发电：https://afdian.net/a/shasha-vault")