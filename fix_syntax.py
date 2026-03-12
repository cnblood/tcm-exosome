import re

filepath = "src/dashboard/app.py"
with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 使用正则表达式精准找到那行损坏的代码，替换为安全无特殊字符的纯英文
pattern = r'ev_cnt\["label"\]\s*=\s*ev_cnt\["has_evidence"\].map\(\{.*?\}\)'
safe_line = 'ev_cnt["label"] = ev_cnt["has_evidence"].map({True:"Has Evidence", False:"No Evidence"})'

content = re.sub(pattern, safe_line, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 成功修复 app.py 中的语法损坏和乱码问题！")
