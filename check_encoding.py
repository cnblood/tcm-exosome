with open('src/dashboard/app.py', 'rb') as f:
    raw = f.read()
print('Encoding guess:', 'utf-8-sig' if raw[:3]==b'\xef\xbb\xbf' else 'other')
print('Bytes at 2495-2505:', raw[2495:2505])
# Try reading with different encodings
for enc in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']:
    try:
        text = raw.decode(enc)
        print(f'SUCCESS with: {enc}')
        break
    except:
        print(f'FAILED: {enc}')
