"""Voice samples for Andrii to choose by ear: the same lines, pauses, speed, finish and loudness, only the voice differs.
Run: python3 tools/voice_samples.py <dir with the Kokoro model> <out dir>  ->  one mp3 a voice + its median pitch."""
import sys, os, json, wave, subprocess
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["KOKORO_DIR"] = sys.argv[1]
import render
from render import F, SR
OUT = sys.argv[2]
story = json.load(open(ROOT / "stories/daniel-lions-den-riviere.json"))
story["lines"] = story["lines"][:8]
V = [("1-current", "am_onyx:0.65+am_michael:0.35", "en-us"),
     ("2-onyx", "am_onyx", "en-us"),
     ("3-fenrir", "am_fenrir", "en-us"),
     ("4-michael", "am_michael", "en-us"),
     ("5-george", "bm_george", "en-gb"),
     ("6-lewis", "bm_lewis", "en-gb"),
     ("7-fable", "bm_fable", "en-gb"),
     ("8-onyx-george", "am_onyx:0.5+bm_george:0.5", "en-us"),
     ("9-nicole", "af_nicole", "en-us")]

def f0(y):
    w, hop, out = int(0.04 * SR), int(0.02 * SR), []
    thr = 0.3 * np.sqrt(np.mean(y ** 2))
    for i in range(0, len(y) - w, hop):
        s = y[i:i + w]
        if np.sqrt(np.mean(s ** 2)) < thr: continue
        s = s - s.mean(); a = np.correlate(s, s, "full")[w - 1:]
        lo, hi = int(SR / 320), int(SR / 60)
        k = lo + int(np.argmax(a[lo:hi]))
        if a[k] > 0.45 * a[0]: out.append(SR / k)
    return float(np.median(out)) if out else 0

for name, spec, lang in V:
    os.environ["KOKORO_VOICE"] = spec
    F["voice"]["kokoro"]["lang"] = lang
    clips = render.speak_lines(story)
    marks, total = render.timeline(story, clips)
    t0 = marks[0][0]
    y = np.zeros(int((marks[-1][1] - t0 + 0.4) * SR), np.float32)
    for (a, b), c in zip(marks, clips):
        i = int((a - t0) * SR); y[i:i + len(c)] += c[:len(y) - i]
    y *= 0.09 / np.sqrt(np.mean(y[np.abs(y) > 0.01] ** 2))            # the same loudness for every variant
    y = np.clip(y, -0.98, 0.98)
    wav = f"{OUT}/{name}.wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "128k", f"{OUT}/{name}.mp3"], check=True)
    os.remove(wav)
    print(f"{name:16s} {spec:32s} {len(y)/SR:5.1f} s  f0 {f0(y):5.0f} Hz  peak {np.abs(y).max():.2f}")
