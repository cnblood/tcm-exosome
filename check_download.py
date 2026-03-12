import os
path = r'C:\Users\ADXA\Downloads\app.py'
if os.path.exists(path):
    print('Size:', os.path.getsize(path), 'bytes')
    with open(path, encoding='utf-8') as f:
        print(f.read(300))
else:
    print('File not found')
