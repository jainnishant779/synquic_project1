import urllib.request
import json
import time

payload = {
    'prompt': 'MAKE AD FOR PARKFNB BARRIER: 15-second 4-stage commercial. Scene 1: Crowded parking bottleneck with vehicle looking for space. Scene 2: High-tech smart ANPR camera detects vehicle and recognizes license plate. Scene 3: Brushless boom barrier elevates rapidly in 0.6 seconds for authorized access. Scene 4: Mobile parking slot booking app and ParkFnB brand reveal.',
    'brand_name': 'ParkFnB Barrier',
    'industry': 'parking_barrier',
    'features': 'ANPR Plate Recognition, 0.6s Rapid Lift, Mobile Slot Booking App',
    'target_audience': 'facility_managers',
    'cta_text': 'Upgrade to ParkFnB Smart Parking',
    'camera_dynamics': 'macro_push',
    'lighting_mood': 'daylight',
    'bgm_genre': 'tech_ambient',
    'director_model': 'nvidia/nemotron-3.5-lightning-30b-a3b',
    'video_provider': 'local_pro_reel',
    'generation_mode': 'pro_commercial',
    'allow_fallback': True,
    'video_task': 'image_to_video',
    'resolution': '1080p',
    'aspect_ratio': '9:16',
    'quality_preset': 'high',
    'duration_s': 15,
    'seed': 42
}

print('Triggering /api/studio/generate for ParkFnB 4-scene commercial...')
t0 = time.time()
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/studio/generate',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print('Status:', resp.status)
        print('Project ID:', data.get('project_id'))
        print('Title:', data.get('title'))
        print('Video URL:', data.get('video_url'))
        print('Category:', data.get('category'))
        print(f'Generation Time: {time.time()-t0:.2f}s')
        print('Manifest URL:', data.get('manifest_url'))
        print('\nQC Report:')
        print(json.dumps(data.get('qc_report'), indent=2))
        print('\nScene Assets & Provenance:')
        for s in data.get('scene_traces', []):
            print(f"  Scene {s.get('scene_num')}: asset={s.get('asset_file')} | motion={s.get('camera_motion')} | clip={s.get('video_clip_url')}")
except Exception as e:
    print('Failed:', e)
    if hasattr(e, 'read'):
        print('Error body:', e.read().decode('utf-8', errors='replace'))
