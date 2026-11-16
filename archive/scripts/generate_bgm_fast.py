import numpy as np
import wave
import subprocess

def create_bgm(filename, style="energetic", duration=35, sr=44100):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    if style == "energetic":
        bpm = 120
        beat_dur = 60.0 / bpm
        
        # 1. Four-on-the-floor kick
        beat_pos = (t % beat_dur) / beat_dur
        kick_mask = beat_pos < 0.2
        kick = np.zeros_like(t)
        kick[kick_mask] = np.sin(2 * np.pi * (130.0 * np.exp(-beat_pos[kick_mask] * 30.0) + 45.0) * beat_pos[kick_mask]) * np.exp(-beat_pos[kick_mask] * 25.0) * 0.4
        
        # 2. Bass pulse
        bass_freq = 110.0 # A2
        bass = np.sin(2 * np.pi * bass_freq * t) * (0.5 + 0.5 * np.cos(2 * np.pi * 4.0 * t)) * 0.2
        
        # 3. Ambient Synth Chords (Am - F - C - G)
        chord_t = (t % 8.0)
        c1 = np.sin(2 * np.pi * 220.0 * t) + np.sin(2 * np.pi * 261.6 * t) + np.sin(2 * np.pi * 329.6 * t)
        c2 = np.sin(2 * np.pi * 174.6 * t) + np.sin(2 * np.pi * 220.0 * t) + np.sin(2 * np.pi * 261.6 * t)
        chord = np.where(chord_t < 4.0, c1, c2) * 0.05
        
        left = kick + bass + chord
        right = kick + bass + chord * 1.05
        
    else: # luxury
        # Cmaj9 ambient slow pad
        notes = [130.8, 196.0, 246.9, 329.6, 392.0]
        pad = np.zeros_like(t)
        for n in notes:
            pad += np.sin(2 * np.pi * n * t) * 0.04
        
        tremolo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * t)
        sub = np.sin(2 * np.pi * 65.4 * t) * 0.12
        left = (pad * tremolo + sub)
        right = (pad * (0.8 + 0.2 * np.cos(2 * np.pi * 0.2 * t)) + sub)

    # Master Normalize
    left = np.clip(left, -0.9, 0.9)
    right = np.clip(right, -0.9, 0.9)
    
    interleaved = np.empty((len(t) * 2,), dtype=np.int16)
    interleaved[0::2] = (left * 32767).astype(np.int16)
    interleaved[1::2] = (right * 32767).astype(np.int16)
    
    with wave.open(filename, 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(interleaved.tobytes())
    print(f"Generated {filename}")

create_bgm("bgm_energetic.wav", "energetic")
create_bgm("bgm_luxury.wav", "luxury")
