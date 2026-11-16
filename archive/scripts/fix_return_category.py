from pathlib import Path

p = Path("d:/research_synquic/web_ec2/main.py")
txt = p.read_text(encoding="utf-8")

old_return = """    return {
        "status": "SUCCESS",
        "project_id": proj_id,
        "title": title,
        "product_entity": product_entity,
        "duration_s": req.duration_s,"""

new_return = """    return {
        "status": "SUCCESS",
        "project_id": proj_id,
        "title": title,
        "category": category,
        "product_entity": product_entity,
        "duration_s": req.duration_s,"""

if old_return in txt:
    txt = txt.replace(old_return, new_return, 1)
    p.write_text(txt, encoding="utf-8")
    print("Successfully added category to return dict!")
else:
    # try with CRLF
    old_crlf = old_return.replace("\n", "\r\n")
    new_crlf = new_return.replace("\n", "\r\n")
    if old_crlf in txt:
        txt = txt.replace(old_crlf, new_crlf, 1)
        p.write_text(txt, encoding="utf-8")
        print("Successfully added category to return dict (CRLF)!")
    else:
        print("Could not find old_return block!")
