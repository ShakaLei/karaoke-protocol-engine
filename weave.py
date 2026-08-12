"""STATION 3 · WEAVE — align words+chords → song.json (canonical score)"""
import sys, json
words = json.load(open(sys.argv[1]))
chords = json.load(open(sys.argv[2]))
out = sys.argv[3]
W, C = words["words"], chords["chords"]
def chord_at(t):
    for c in C:
        if c["t0"] <= t < c["t1"]: return c["c"]
    return C[-1]["c"] if C else ""
# group words into lines by gaps > 1.2s
lines, cur, last_end = [], [], None
for w in W:
    if last_end is not None and w["t0"] - last_end > 1.2 and cur:
        lines.append(cur); cur=[]
    cur.append(w); last_end = w["t1"]
if cur: lines.append(cur)
score=[]
for ln in lines:
    score.append({
        "t0": ln[0]["t0"], "t1": ln[-1]["t1"],
        "text": " ".join(w["w"] for w in ln).strip(),
        "chord": chord_at(ln[0]["t0"]),
        "words": ln,
    })
json.dump({"bpm": chords.get("bpm"), "lines": score}, open(out,"w"))
print(f"WEAVE ✓ {len(score)} lines → {out}")
