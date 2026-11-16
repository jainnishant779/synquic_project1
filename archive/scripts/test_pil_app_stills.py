import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_pro_app_visuals(brand_name: str, headline: str, subtitle: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1080, 1920
    
    font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    shots_data = [
        {"shot": 1, "title": brand_name.upper(), "badge": "VERIFIED HOME SERVICE APP", "feat": "PLUMBING • CLEANING • ELECTRICAL", "cta": "Instant Doorstep Arrival in 30 Mins", "accent": (16, 185, 129)},
        {"shot": 2, "title": "CERTIFIED EXPERTS", "badge": "BACKGROUND CHECKED PROS", "feat": "FIXES • REPAIRS • DEEP CLEAN", "cta": "Transparent Pricing • Zero Hidden Fees", "accent": (59, 130, 246)},
        {"shot": 3, "title": f"GET {brand_name.upper()}", "badge": "50,000+ HOMES TRUST US", "feat": "5-STAR RATED HOMECARE", "cta": "Download on iOS & Android Today", "accent": (245, 158, 11)}
    ]

    paths = []
    for s in shots_data:
        idx = s["shot"]
        im = Image.new("RGB", (width, height), (10, 15, 29))
        draw = ImageDraw.Draw(im)

        # Gradient background
        for y in range(height):
            r = int(12 + (y / height) * 18)
            g = int(18 + (y / height) * 28)
            b = int(36 + (y / height) * 45)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Glowing phone card in center
        cx, cy = width // 2, height // 2 - 60
        card_w, card_h = 780, 1100
        x0, y0 = cx - card_w // 2, cy - card_h // 2
        x1, y1 = cx + card_w // 2, cy + card_h // 2

        # Card outer border glow
        draw.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], radius=44, fill=(30, 41, 59), outline=s["accent"], width=3)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=40, fill=(15, 23, 42))

        # Phone notch & status
        draw.rounded_rectangle([cx - 90, y0 + 16, cx + 90, y0 + 44], radius=14, fill=(2, 6, 23))

        # App Brand Header
        try:
            f_title = ImageFont.truetype(font_bold, 64)
            f_badge = ImageFont.truetype(font_bold, 24)
            f_body = ImageFont.truetype(font_bold, 36)
            f_sub = ImageFont.truetype(font_reg, 30)
        except:
            f_title = f_badge = f_body = f_sub = ImageFont.load_default()

        # Logo Circle
        draw.ellipse([cx - 55, y0 + 100, cx + 55, y0 + 210], fill=s["accent"])
        draw.text((cx - 18, y0 + 125), s["title"][0], fill=(255, 255, 255), font=f_title)

        # Brand Title
        draw.text((cx, y0 + 260), s["title"], fill=(255, 255, 255), font=f_title, anchor="mm")
        
        # Badge
        badge_text = s["badge"]
        draw.rounded_rectangle([cx - 240, y0 + 310, cx + 240, y0 + 360], radius=16, fill=(30, 58, 138, 80), outline=s["accent"], width=2)
        draw.text((cx, y0 + 335), badge_text, fill=s["accent"], font=f_badge, anchor="mm")

        # Feature Box
        draw.rounded_rectangle([x0 + 50, y0 + 420, x1 - 50, y0 + 640], radius=24, fill=(30, 41, 59))
        draw.text((cx, y0 + 490), s["feat"], fill=(241, 245, 249), font=f_body, anchor="mm")
        draw.text((cx, y0 + 560), "Verified 24/7 Service • On-Demand", fill=(148, 163, 184), font=f_sub, anchor="mm")

        # Bottom Action Bar inside phone
        draw.rounded_rectangle([x0 + 50, y0 + 720, x1 - 50, y0 + 820], radius=20, fill=s["accent"])
        draw.text((cx, y0 + 770), "BOOK SERVICE NOW", fill=(15, 23, 42), font=f_body, anchor="mm")

        # Subtitle under phone
        draw.text((cx, y0 + 920), s["cta"], fill=(226, 232, 240), font=f_sub, anchor="mm")

        p = out_dir / f"app_still_{idx}.png"
        im.save(p, "PNG")
        paths.append(p)
        print(f"Created {p} ({p.stat().st_size} bytes)")

    return paths

if __name__ == "__main__":
    out = Path("/tmp/test_homingo_stills")
    create_pro_app_visuals("Homingo", "Home Services", "Book in 30s", out)
