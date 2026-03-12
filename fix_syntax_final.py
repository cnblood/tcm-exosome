filepath = 'src/dashboard/app.py'
with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

with open(filepath, 'w', encoding='utf-8') as f:
    for line in lines:
        # 只要找到包含这句代码的行，强制替换为无乱码、带闭合引号的安全版本
        if 'ev_cnt["has_evidence"].map' in line:
            f.write('            ev_cnt["label"] = ev_cnt["has_evidence"].map({True:"Has Evidence", False:"No Evidence"})\n')
        else:
            f.write(line)

print("✅ app.py 语法修复成功！")
