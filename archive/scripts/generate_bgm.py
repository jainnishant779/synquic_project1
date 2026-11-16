import math, struct, wave, subprocess
from pathlib import Path

def generate_commercial_bgm(output_wav, style="energetic", duration=30, sample_rate=44100):
    total_samples = int(duration * sample_rate)
    frames = bytearray()
    bpm = 120 if style == "energetic" else 75
    beat_dur = 60.0 / bpm
    
    for i in range(total_samples):
        t = i / sample_rate
        left = 0.0
        right = 0.0
        
        if style == "energetic":
            # 1. Kick on each quarter note (120 bpm)
            beat_pos = (t % beat_dur) / beat_dur
            if beat_pos < 0.2:
                kick_env = math.exp(-beat_pos * 28.0)
                kick_freq = 130.0 * math.exp(-beat_pos * 35.0) + 45.0
                kick_val = math.sin(2.0 * math.pi * kick_freq * beat_pos) * kick_env * 0.35
                left += kick_val
                right += kick_val
                
            # 2. Bass synth line (8th note pulse)
            bass_beat = int(t / (beat_dur / 2)) % 8
            bass_freqs = [110.0, 110.0, 130.8, 110.0, 87.3, 87.3, 98.0, 98.0]
            cur_bfreq = bass_freqs[bass_beat]
            b_env = math.exp(-(t % (beat_dur / 2)) * 8.0)
            bass_val = math.sin(2.0 * math.pi * cur_bfreq * t) * b_env * 0.18
            left += bass_val * 0.8
            right += bass_val * 0.8
            
            # 3. Stereo Hi-Hat
            hat_pos = (t % (beat_dur / 2)) / (beat_dur / 2)
            if 0.4 < hat_pos < 0.7:
                h_env = math.exp(-(hat_pos - 0.4) * 35.0)
                noise = (math.sin(i * 12345.678) % 1.0) * 2.0 - 1.0
                left += noise * h_env * 0.05
                right -= noise * h_env * 0.05
                
            # 4. Melodic Synth Pad / Chords
            chord_idx = int(t / (beat_dur * 4)) % 4
            chord_notes = [
                [220.0, 261.6, 329.6],  # Am
                [174.6, 220.0, 261.6],  # F
                [261.6, 329.6, 392.0],  # C
                [196.0, 246.9, 293.7]   # G
            ][chord_idx]
            
            pad_l = 0.0
            pad_r = 0.0
            for note in chord_notes:
                pad_l += math.sin(2.0 * math.pi * note * t + 0.1) * 0.035
                pad_r += math.sin(2.0 * math.pi * (note * 1.003) * t + 0.5) * 0.035
                
            left += pad_l
            right += pad_r
            
        else: # Luxury / Ambient
            chord_idx = int(t / 8.0) % 2
            notes = [
                [130.8, 196.0, 246.9, 329.6, 392.0], # Cmaj9
                [174.6, 220.0, 261.6, 329.6, 440.0]  # Fmaj7
            ][chord_idx]
            
            tremolo = 0.7 + 0.3 * math.sin(2.0 * math.pi * 0.25 * t)
            pad_l = 0.0
            pad_r = 0.0
            for n_idx, n in enumerate(notes):
                pan = (n_idx / len(notes)) * 0.6 - 0.3
                sine_val = (math.sin(2.0 * math.pi * n * t) + 0.3 * math.sin(4.0 * math.pi * n * t)) * 0.04
                pad_l += sine_val * (1.0 - pan) * tremolo
                pad_r += sine_val * (1.0 + pan) * tremolo
                
            sub = math.sin(2.0 * math.pi * 65.4 * t) * 0.12
            left += pad_l + sub
            right += pad_r + sub

        left = max(-0.95, min(0.95, left))
        right = max(-0.95, min(0.95, right))
        frames.extend(struct.pack('<hh', int(left * 32767), int(right * 32767)))

    with wave.open(str(output_wav), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames)
    print(f"Generated {output_wav}")

generate_commercial_bgm("bgm_energetic.wav", style="energetic", duration=35)
generate_commercial_bgm("bgm_luxury.wav", style="luxury", duration=35)
