"""STATION 1 · LISTEN — whisper w/ word timestamps → words.json"""
import os, sys, json
os.environ.setdefault('HF_HOME','/workspace/.cache/hf')
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(src, language=(os.environ.get("KP_LANG") or None), word_timestamps=True, vad_filter=False, condition_on_previous_text=True)
words=[]
for s in segments:
    for w in (s.words or []):
        words.append({"w": w.word, "t0": round(w.start,2), "t1": round(w.end,2)})
json.dump({"lang": info.language, "words": words}, open(out,"w"))
print(f"LISTEN ✓ {len(words)} words, lang={info.language} → {out}")
