content = open('src/database/tcm_pharmacopoeia_init.py', encoding='utf-8').read()
content = content.replace("'/home/claude/tcm_pharmacopoeia_init.sql'", "'tcm_pharmacopoeia_init.sql'")
open('src/database/tcm_pharmacopoeia_init.py', 'w', encoding='utf-8').write(content)
print('Fixed!')
