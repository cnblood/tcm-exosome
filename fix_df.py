content = open('Dockerfile').read()
old = 'RUN mkdir -p /app/data /app/logs'
new = 'RUN mkdir -p /app/data /app/logs\nCOPY data/tcm_exosome.db /app/data/tcm_exosome.db'
content = content.replace(old, new)
open('Dockerfile', 'w').write(content)
print('OK:', 'tcm_exosome.db' in content)
