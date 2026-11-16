import re

# 1. Update web_ec2/main.py
with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    main_code = f.read()

# Expand GenerateVideoRequest
old_gvr = """class GenerateVideoRequest(BaseModel):
    prompt: str
    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    image_model: str = "flux2_klein_4b"                 # Image Generation Model
    video_provider: str = "nvidia_nim"                  # Strictly NVIDIA NIM under Quality-First policy
    video_model: str = "wan-ai/wan2.2"                  # NVIDIA Wan2.2 14B Video NIM SOTA
    generation_mode: str = "full_ai"                    # "full_ai" or "hybrid_fallback"
    video_task: str = "image_to_video"                  # "image_to_video" (I2V) or "text_to_video" (T2V)
    resolution: str = "1080p"                           # "1080p" Full HD or "720p" HD
    aspect_ratio: str = "16:9"                          # "16:9" or "9:16"
    quality_preset: str = "high"                        # "high" (50 steps) or "standard" (30 steps)
    audio_voice: str = "auto"                           # edge-tts voice or "auto"
    motion_style: str = "kenburns_cinematic"            # Image Motion Fallback preset (FFmpeg)
    reference_assets: List[str] = []                    # Uploaded product reference asset IDs
    max_scene_attempts: int = 2
    allow_fallback: bool = False                        # When False, rejects execution if GPU host is unreachable
    duration_s: int = 15
    style: str = "Luxury Minimalist" """

new_gvr = """class GenerateVideoRequest(BaseModel):
    prompt: str
    brand_name: Optional[str] = None                    # Explicit Brand / Entity Name
    industry: Optional[str] = None                      # Industry Sector / Category
    features: Optional[str] = None                      # Core Value Proposition / Key Features
    target_audience: Optional[str] = None               # Target Demographic / Audience
    camera_dynamics: Optional[str] = "macro_push"       # Camera Movement & Dynamics
    lighting_mood: Optional[str] = "studio_clean"       # Lighting & Mood Aesthetic
    color_grading: Optional[str] = "vibrant"            # Color Grading & Visual Tone
    bgm_genre: Optional[str] = "tech_ambient"           # Background Music Genre
    cta_text: Optional[str] = None                      # Call To Action / Closing Tagline
    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    image_model: str = "flux2_klein_4b"                 # Image Generation Model
    video_provider: str = "nvidia_nim"                  # Strictly NVIDIA NIM under Quality-First policy
    video_model: str = "wan-ai/wan2.2"                  # NVIDIA Wan2.2 14B Video NIM SOTA
    generation_mode: str = "full_ai"                    # "full_ai" or "hybrid_fallback"
    video_task: str = "image_to_video"                  # "image_to_video" (I2V) or "text_to_video" (T2V)
    resolution: str = "1080p"                           # "1080p" Full HD or "720p" HD
    aspect_ratio: str = "16:9"                          # "16:9" or "9:16"
    quality_preset: str = "high"                        # "high" (50 steps) or "standard" (30 steps)
    audio_voice: str = "auto"                           # edge-tts voice or "auto"
    motion_style: str = "kenburns_cinematic"            # Image Motion Fallback preset (FFmpeg)
    reference_assets: List[str] = []                    # Uploaded product reference asset IDs
    max_scene_attempts: int = 2
    allow_fallback: bool = False                        # When False, rejects execution if GPU host is unreachable
    duration_s: int = 15
    style: str = "Luxury Minimalist" """

# Add parking_barrier to PRODUCT_PROFILES
parking_profile = """    "parking_barrier": {
        "keywords": ["barrier", "parking", "parkfnb", "boom barrier", "gate", "toll", "rfid", "access control", "security gate", "turnstile", "smart parking", "boom"],
        "default_title": "ParkFnB Intelligent Automated Boom Barrier Commercial",
        "default_entity": "ParkFnB Smart Boom Barrier",
        "voice": "en-US-ChristopherNeural",
        "bgm": "bgm_energetic.mp3",
        "bgm_volume": 0.22,
        "style_mood": "High-Tech Industrial Security, Clean Architectural Daylight & Laser Precision",
        "stills": ["barrier_hero.jpg", "barrier_action.jpg", "barrier_finish.jpg"],
        "default_shots": [
            {
                "shot_num": 1, "duration_s": 5, "type": "Hero Product Reveal",
                "visual_prompt": "Ultra-sleek automated parking boom barrier with illuminated LED arm in front of modern corporate entrance, crisp morning light",
                "camera": "Slow macro push-in on high-speed boom mechanism",
                "narration": "Parking bottlenecks end here. Meet the future of seamless vehicle access.",
                "on_screen_text": "INSTANT RFID CLEARANCE",
                "dialect_wan": "Automated boom barrier lifting smoothly, optical vehicle sensor tracking",
                "dialect_veo": "High-tech commercial hero shot of heavy-duty parking barrier with illuminated LED guidance"
            },
            {
                "shot_num": 2, "duration_s": 5, "type": "Action & Clearance Speed",
                "visual_prompt": "Luxury sedan approaching modern parking gate as boom barrier lifts in ultra-rapid 0.6 seconds with smooth brushless motor",
                "camera": "High-speed tracking shot as vehicle glides through entry lane",
                "narration": "Lightning-fast 0.6 second clearance. Military-grade anti-crash radar protection.",
                "on_screen_text": "0.6S RAPID LIFT",
                "dialect_wan": "Rapid boom arm lift, smooth hydraulic damping, anti-collision radar active",
                "dialect_veo": "Cinematic automotive lane entrance, barrier arm elevating with bright green LED indicator"
            },
            {
                "shot_num": 3, "duration_s": 5, "type": "Architectural Finish & CTA",
                "visual_prompt": "Wide architectural view of multi-lane commercial parking entrance with synchronized boom barriers and smart digital display",
                "camera": "Subtle dolly back and focus pull on ParkFnB signature branding",
                "narration": "Zero delays. One hundred percent uptime. Upgrade your facility with ParkFnB today.",
                "on_screen_text": "PARKFNB BARRIERS",
                "dialect_wan": "Synchronized parking barriers, multi-lane facility, high-traffic commercial flow",
                "dialect_veo": "Corporate architectural packshot of high-tech parking facility at dusk with glowing LED lanes"
            }
        ]
    },
"""

main_code = main_code.replace("PRODUCT_PROFILES = {\n", "PRODUCT_PROFILES = {\n" + parking_profile, 1)

# Ensure Optional is imported
if "from typing import " in main_code and "Optional" not in main_code:
    main_code = main_code.replace("from typing import ", "from typing import Optional, ")

# Replace GVR
normalized_code = main_code.replace("\r\n", "\n")
normalized_old_gvr = old_gvr.replace("\r\n", "\n")
normalized_new_gvr = new_gvr.replace("\r\n", "\n")

if normalized_old_gvr in normalized_code:
    normalized_code = normalized_code.replace(normalized_old_gvr, normalized_new_gvr, 1)
else:
    # Fuzzy match GVR class
    normalized_code = re.sub(r"class GenerateVideoRequest\(BaseModel\):.*?(?=\n\nPRODUCT_PROFILES)", normalized_new_gvr, normalized_code, flags=re.DOTALL)

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(normalized_code)

print("Updated main.py with expanded GenerateVideoRequest and parking_barrier profile!")
