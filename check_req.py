import subprocess
result = subprocess.run(['cat', 'requirements.txt'], capture_output=True, text=True)
print(result.stdout)
