with open('src/dashboard/app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

import re
# 找所有破损的字符串字面量并修复
content = content.replace('Has Evidence \ufffd?', 'Has Evidence \u2b50')
content = content.replace('Has Evidence \u731b?', 'Has Evidence \u2b50')
content = content.replace('"Has Evidence \ufffd', '"Has Evidence \u2b50"')

# 用正则找所有未闭合的字符串
lines = content.split('\n')
for i, line in enumerate(lines):
    if ('Has Evidence' in line or 'Herbs w/' in line) and line.count('"') % 2 != 0:
        print(f"Broken line {i+1}: {repr(line)}")
        # 替换破损部分
        lines[i] = re.sub(r'"Has Evidence [^"]*$', '"Has Evidence \u2b50"', line)
        print(f"Fixed: {repr(lines[i])}")

content = '\n'.join(lines)
with open('src/dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
