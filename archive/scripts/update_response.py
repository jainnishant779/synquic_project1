from pathlib import Path

p = Path("d:/research_synquic/web_ec2/main.py")
txt = p.read_text(encoding="utf-8")
old_str = '"title": title,\n        "product_entity": product_entity,'
new_str = '"title": title,\n        "category": category,\n        "product_entity": product_entity,\n        "aspect_ratio": req.aspect_ratio,'

if old_str in txt:
    txt = txt.replace(old_str, new_str, 1)
    p.write_text(txt, encoding="utf-8")
    print("Updated response dictionary successfully!")
else:
    # Try CRLF
    old_crlf = old_str.replace('\n', '\r\n')
    new_crlf = new_str.replace('\n', '\r\n')
    if old_crlf in txt:
        txt = txt.replace(old_crlf, new_crlf, 1)
        p.write_text(txt, encoding="utf-8")
        print("Updated response dictionary (CRLF) successfully!")
    else:
        print("Pattern not found!")
