"""Original deterministic synthesized travel-game audio; no sampled recordings.

Run with Python's standard library. Writes source WAVs and consumer copies.
Music is a gentle 16-bar, 80 BPM marimba-like loop in C major.
"""
from array import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import wave

RATE = 22050
ROOT = Path(__file__).resolve().parent
CLIENT = ROOT.parents[1] / 'jigsaw-travel-client' / 'assets' / 'audio'
CLIENT.mkdir(parents=True, exist_ok=True)

def tone(buffer, start, note, duration, gain=0.1, soft=False):
    frequency = 440 * 2 ** ((note - 69) / 12)
    count = int(duration * RATE)
    offset = int(start * RATE)
    for i in range(count):
        t = i / RATE
        attack = min(1, t / 0.014)
        release = min(1, (duration - t) / 0.07)
        decay = math.exp(-t * (2.8 if soft else 7))
        phase = 2 * math.pi * frequency * t
        value = math.sin(phase) + 0.22 * math.sin(phase * 2) + 0.07 * math.sin(phase * 3)
        # Circular rendering preserves the reverb-like tails across the loop edge.
        buffer[(offset + i) % len(buffer)] += gain * value * attack * release * decay

manifest = []
def save(name, buffer, loop=False):
    peak = max(abs(x) for x in buffer)
    assert 0 < peak < 0.85, (name, peak)
    pcm = array('h', (round(x * 32767) for x in buffer))
    path = ROOT / (name + '.wav')
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    shutil.copy2(path, CLIENT / path.name)
    manifest.append({'file': path.name, 'seconds': len(buffer) / RATE,
                     'peak': round(peak, 5), 'loop': loop,
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

beat = 0.75
music = array('d', [0.0]) * int(16 * 4 * beat * RATE)
chords = [(48, 55, 60, 64), (45, 52, 57, 60), (41, 48, 53, 57), (43, 50, 55, 59)]
melodies = [(76, 79, 81, 79), (76, 72, 74, 76), (77, 76, 72, 69), (74, 71, 67, 72)]
for bar in range(16):
    chord = chords[(bar // 2) % 4]
    for step in range(8):
        tone(music, (bar * 4 + step / 2) * beat, chord[step % 4], 1.8, 0.035, True)
    if bar % 2 == 0:
        for step, note in enumerate(melodies[(bar // 4) % 4]):
            tone(music, (bar * 4 + step * 0.75 + 0.25) * beat, note, 1.1, 0.05, True)
save('sunlit-stroll', music, True)

for name, duration, notes in [
    ('place', 0.4, [(0, 79, 0.3, 0.12), (0.045, 84, 0.3, 0.08)]),
    ('soft-return', 0.25, [(0, 60, 0.22, 0.065)]),
    ('page', 0.2, [(0, 72, 0.16, 0.04)]),
    ('booster', 0.7, [(0, 72, 0.4, 0.10), (0.10, 76, 0.4, 0.10), (0.20, 79, 0.45, 0.10)]),
    ('complete', 1.7, [(0, 72, 0.6, 0.11), (0.18, 76, 0.6, 0.11), (0.36, 79, 0.7, 0.11), (0.6, 84, 1.0, 0.13)]),
]:
    buffer = array('d', [0.0]) * int(duration * RATE)
    for start, note, length, gain in notes:
        tone(buffer, start, note, length, gain)
    save(name, buffer)

(ROOT / 'manifest.json').write_text(json.dumps({
    'status': 'production candidate; listening and device approval pending',
    'source': 'Original procedural synthesis and composition in generate_audio.py; no third-party samples',
    'sampleRate': RATE, 'channels': 1, 'bits': 16, 'assets': manifest,
}, indent=2) + '\n', encoding='utf-8')
print(f'Generated {len(manifest)} original audio assets without clipping.')
