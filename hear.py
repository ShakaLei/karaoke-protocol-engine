"""STATION 2 · HEAR — chroma → chord timeline (maj/min templates, per beat-window) → chords.json"""
import sys, json, numpy as np, librosa
src, out = sys.argv[1], sys.argv[2]
y, sr = librosa.load(src, sr=22050, mono=True)
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=2048)
bt = librosa.frames_to_time(beats, sr=sr, hop_length=2048)
if len(bt) < 2: bt = np.arange(0, librosa.get_duration(y=y, sr=sr), 2.0)
NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def template(root, minor):
    t = np.zeros(12); t[root]=1; t[(root+(3 if minor else 4))%12]=0.8; t[(root+7)%12]=0.9; return t
TEMPS = [(r,m,template(r,m)) for r in range(12) for m in (0,1)]
chords=[]
for i in range(len(bt)):
    t0 = bt[i]; t1 = bt[i+1] if i+1 < len(bt) else t0 + 2.0
    f0, f1 = int(t0*sr/2048), int(t1*sr/2048)
    if f1 <= f0: continue
    c = chroma[:, f0:f1].mean(axis=1)
    if c.max() < 1e-6: continue
    c = c / (np.linalg.norm(c)+1e-9)
    best, bs = None, -1
    for r,m,t in TEMPS:
        s = float(np.dot(c, t/(np.linalg.norm(t)+1e-9)))
        if s > bs: bs, best = s, (r,m)
    name = NOTES[best[0]] + ("m" if best[1] else "")
    if chords and chords[-1]["c"] == name: chords[-1]["t1"] = round(float(t1),2)
    else: chords.append({"c": name, "t0": round(float(t0),2), "t1": round(float(t1),2)})
json.dump({"bpm": round(float(tempo[0] if hasattr(tempo,'__len__') else tempo),1), "chords": chords}, open(out,"w"))
print(f"HEAR ✓ {len(chords)} chord segments → {out}")
