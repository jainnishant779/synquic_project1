import edge_tts, asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    print("=== English Voices ===")
    for v in voices:
        if v["Locale"].startswith("en"):
            print(v["ShortName"], " -", v["FriendlyName"], v.get("Gender",""))

asyncio.run(list_voices())
