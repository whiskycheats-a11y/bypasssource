import sys
with open('whitelist_bot.py', 'rb') as f:
    c = f.read()

try:
    if c.startswith(b'\xff\xfe'):
        # UTF-16 LE BOM
        c = c.decode('utf-16')
    else:
        # Check if contains lots of nulls
        if b'\x00' in c:
            c = c.decode('utf-16le')
        else:
            c = c.decode('utf-8')
except Exception as e:
    c = c.decode('utf-8', errors='ignore')

with open('whitelist_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Fixed encoding.")
