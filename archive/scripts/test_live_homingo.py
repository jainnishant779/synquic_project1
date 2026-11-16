import urllib.request
import json
import time

payload = {
    'prompt': 'make ad for homingo app -an home service provider app: Verified background-checked professionals for emergency plumbing, electrical repairs, and deep cleaning, arriving in 30 minutes with transparent pricing.',
    'brand_name': 'Homingo',
    'industry': 'home_services',
    'features': 'Verified Experts in 30 Min, Emergency Plumbing & Repairs, Transparent Pricing',
    'target_audience': 'busy_homeowners',
    'cta_text': 'Download Homingo Today',
    'camera_dynamics': 'macro_push',
    'lighting_mood': 'daylight',
    'bgm_genre': 'energetic',
    'director_model': 'nvidia/nemotron-3.5-lightning-30b-a3b',
    'video_provider': 'local_pro_reel',
    'generation_mode': 'full_ai',
    'video_task': 'image_to_video',
    'resolution': '1080p',
    'aspect_ratio': '9:16',
    'quality_preset': 'high',
    'duration_s': 15,
    'seed': 42
}

print('Triggering /api/studio/generate for Homingo 4-scene commercial reel...')
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
        print('QC Report:', json.dumps(data.get('qc_report'), indent=2))
        print('\nStoryboard Scenes:')
        for s in data.get('storyboard', []):
            print(f"  Shot {s.get('shot_num')}: {s.get('type')} ({s.get('duration_s')}s) -> {s.get('on_screen_text')} | Voice: {s.get('narration')}")
except Exception as e:
    print('Failed:', e)
    if hasattr(e, 'read'):
        print('Error body:', e.read().decode('utf-8', errors='replace'))
