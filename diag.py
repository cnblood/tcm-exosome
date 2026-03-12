import os
# 写入新版标识测试
path = r'src\dashboard\app.py'
with open(path, 'r', encoding='utf-8') as f:
    old = f.read()
print('旧版大小:', len(old), 'bytes')
print('包含Herb Evidence:', 'Herb Evidence' in old)
print('包含SUPABASE:', 'SUPABASE' in old)
