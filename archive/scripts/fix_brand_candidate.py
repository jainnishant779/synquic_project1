with open('web_ec2/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

old = """    # Support explicit Brand Name from user parameter
    if getattr(req, "brand_name", None) and req.brand_name.strip():
        brand_display = req.brand_name.strip()"""

new = """    # Support explicit Brand Name from user parameter
    if getattr(req, "brand_name", None) and req.brand_name.strip():
        brand_candidate = req.brand_name.strip()
        brand_display = brand_candidate"""

code_norm = code.replace('\r\n', '\n')
assert old.replace('\r\n', '\n') in code_norm, 'old string not found'
code_norm = code_norm.replace(old.replace('\r\n', '\n'), new.replace('\r\n', '\n'), 1)

with open('web_ec2/main.py', 'w', encoding='utf-8') as f:
    f.write(code_norm)

print('Successfully fixed brand_candidate!')
