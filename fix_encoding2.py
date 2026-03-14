import sys

with open('whitelist_bot.py', 'rb') as f:
    c = f.read()

# Currently c might be UTF-16LE without BOM but read as bytes
# Wait, if `fix_encoding.py` previously did `c = c.decode('utf-8')` on a utf-16le file, that would return a string with nulls. Then `write(c)` with `encoding='utf-8'` would write it back with nulls. So the file on disk is literally utf-8 encoded, but contains null characters.

# We can remove the null bytes, or we can just read it again as utf-16le
cleaned = c.replace(b'\x00', b'')
with open('whitelist_bot.py', 'wb') as f:
    f.write(cleaned)

print("Fixed null bytes.")
