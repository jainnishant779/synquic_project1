import re

with open('web_ec2/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

ids_in_js = re.findall(r"document\.getElementById\(['\"]([^'\"]+)['\"]\)", content)
ids_in_html = set(re.findall(r'id=["\']([^"\']+)["\']', content))

missing = []
for el_id in sorted(set(ids_in_js)):
    if el_id not in ids_in_html:
        missing.append(el_id)

print(f"Total getElementById calls: {len(ids_in_js)}, Unique IDs queried: {len(set(ids_in_js))}")
print("IDs queried in JS but MISSING in HTML:")
for m in sorted(missing):
    print(f"  - {m}")
