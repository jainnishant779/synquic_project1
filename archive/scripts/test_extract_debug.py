import sys
sys.path.insert(0, "/home/ubuntu/synquic_app")
from main import extract_json_from_text

sample = """{
  "title": "Homingo: Fast Home Service",
  "product": "homingo App",
  "shots": [
    {
      "shot_num": 1,
      "duration_s": 5,
      "type": "Cinematic Macro Push-in",
      "visual_prompt": "Modern architectural interior...",
      "camera": "Cinematic Macro Push-in",
      "narration": "When home repairs pop up, Homingo has you covered.",
      "on_screen_text": "All Types of Home Service"
    }
  ]
}"""

res = extract_json_from_text(sample)
print("EXTRACTED:", res is not None, res.get("title") if res else None)
