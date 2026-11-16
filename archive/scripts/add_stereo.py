with open('web_ec2/main.py', 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('\r\n', '\n')
old_line = '"-c:a", "aac", "-b:a", "192k",'
new_line = '"-c:a", "aac", "-b:a", "192k", "-ac", "2",'
s = s.replace(old_line, new_line)
with open('web_ec2/main.py', 'w', encoding='utf-8') as f:
    f.write(s)
print('Updated stereo flag in web_ec2/main.py')
