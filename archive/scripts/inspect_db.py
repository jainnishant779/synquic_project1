import sqlite3
import json

conn = sqlite3.connect('/home/ubuntu/synquic_app/data/synquic_eval_studio.db')
cursor = conn.cursor()
cursor.execute('SELECT id, created_at, prompt, product_entity, title, video_url, storyboard_json FROM studio_projects ORDER BY created_at DESC LIMIT 10')
for row in cursor.fetchall():
    print("=" * 60)
    print(f"ID: {row[0]}")
    print(f"Created: {row[1]}")
    print(f"Prompt: {row[2]}")
    print(f"Entity: {row[3]}")
    print(f"Title: {row[4]}")
    print(f"URL: {row[5]}")
    try:
        sb = json.loads(row[6])
        if isinstance(sb, dict):
            print(f"Category: {sb.get('category')}")
            print(f"Product: {sb.get('product')}")
            shots = sb.get('shots', [])
            print(f"Shots count: {len(shots)}")
            for i, s in enumerate(shots):
                print(f"  Shot {i+1}: {s.get('shot_name') or s.get('title')} | Visual: {s.get('visual_prompt', '')[:60]} | Audio: {s.get('voiceover', '')[:60]}")
    except Exception as e:
        print(f"Storyboard parse error: {e}")
