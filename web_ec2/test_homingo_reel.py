import os, sys, time, json, urllib.request, urllib.parse, subprocess
from pathlib import Path

out_dir = Path('/home/ubuntu/synquic_app/static/media/test_homingo')
out_dir.mkdir(parents=True, exist_ok=True)

shots = [
    {
        'num': 1,
        'tagline': 'HOME EMERGENCIES SOLVED',
        'terms': ['plumbing leak', 'faucet leak', 'pipe repair', 'water damage'],
        'motion': 'push_in'
    },
    {
        'num': 2,
        'tagline': 'VERIFIED EXPERTS IN 30 MIN',
        'terms': ['service technician', 'repairman tools', 'electrician maintenance'],
        'motion': 'tracking'
    },
    {
        'num': 3,
        'tagline': 'DOWNLOAD HOMINGO TODAY',
        'terms': ['Luxury Living Room Interior Design in Kolkata', 'modern luxury living room', 'clean home interior'],
        'motion': 'pull_back'
    }
]

def search_wikimedia_or(terms):
    for term in terms:
        url = f'https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={urllib.parse.quote(term)}&gsrnamespace=6&gsrlimit=20&prop=imageinfo&iiprop=url|size|mime'
        req = urllib.request.Request(url, headers={'User-Agent': 'SynquicStudio/1.0 (contact@synquic.com)'})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.loads(r.read())
                pages = d.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    infos = pdata.get('imageinfo', [])
                    if infos and 'url' in infos[0]:
                        u = infos[0]['url']
                        mime = infos[0].get('mime', '')
                        w = infos[0].get('width', 0)
                        h = infos[0].get('height', 0)
                        if ('image/jpeg' in mime or 'image/png' in mime) and w >= 600 and h >= 600:
                            print(f"Found for '{term}': {u[:70]} ({w}x{h})")
                            return u
        except Exception as ex:
            print("Search err:", ex)
    return None

shot_files = []
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

for s in shots:
    img_url = search_wikimedia_or(s['terms'])
    print(f"Shot {s['num']} URL:", img_url)
    img_path = out_dir / f"raw_shot_{s['num']}.jpg"
    req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        img_path.write_bytes(resp.read())
    
    mp4_path = out_dir / f"scene_{s['num']}.mp4"
    duration = 5
    fps = 25
    frames = duration * fps
    
    if s['motion'] == 'push_in':
        pan_filt = f"zoompan=z='min(zoom+0.0014,1.18)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
    elif s['motion'] == 'tracking':
        pan_filt = f"zoompan=z=1.08:d={frames}:x='(iw-iw/zoom)*(on/{frames})':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
    else:
        pan_filt = f"zoompan=z='max(1.001,1.16-0.0012*on)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
        
    tagline_esc = s['tagline'].replace("'", "\\'").replace(":", "\\:")
    
    filter_complex = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{pan_filt},"
        f"eq=contrast=1.12:saturation=1.22,"
        f"drawbox=x=0:y=1480:w=1080:h=340:color=black@0.60:t=fill,"
        f"drawtext=text='HOMINGO':fontfile='{font_path}':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=1540:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
        f"drawtext=text='{tagline_esc}':fontfile='{font_path}':fontsize=30:fontcolor=#38bdf8:x=(w-text_w)/2:y=1620:shadowcolor=black@0.9:shadowx=2:shadowy=2"
    )
    
    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-loop', '1', '-i', str(img_path),
        '-vf', filter_complex,
        '-t', str(duration),
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
        '-pix_fmt', 'yuv420p', str(mp4_path)
    ]
    subprocess.run(cmd, check=True)
    shot_files.append(mp4_path)
    print(f"Rendered Shot {s['num']} MP4 successfully.")

concat_list = out_dir / 'concat.txt'
concat_list.write_text('\n'.join([f"file '{p.resolve()}'" for p in shot_files]))
final_mp4 = out_dir / 'homingo_commercial_reel.mp4'

cmd_concat = [
    'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
    '-f', 'concat', '-safe', '0', '-i', str(concat_list),
    '-c', 'copy', str(final_mp4)
]
subprocess.run(cmd_concat, check=True)
print("FINAL HOMINGO REEL READY:", final_mp4, "Size:", final_mp4.stat().st_size)
