with open('src/dashboard/app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'evidence' in line and 'Herbs w' in line:
        print(f"Line {i+1}: {repr(line)}")
        lines[i] = '        (evidence,"Herbs w/ Evidence",  "\u2b50"),\n'
        print(f"Fixed to: {repr(lines[i])}")

with open('src/dashboard/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Done")
