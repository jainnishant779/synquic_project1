import asyncio
import edge_tts
from pathlib import Path

async def main():
    text = "Wake up to pure, organic botanical hydration. Cold-pressed active nutrients for an all-day natural radiance. AuraGlow. Your morning radiance ritual."
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    out_file = Path("/home/ubuntu/synquic_app/static/media/test_voice.mp3")
    await communicate.save(str(out_file))
    print(f"Voice saved to {out_file}, size: {out_file.stat().st_size} bytes")

asyncio.run(main())
