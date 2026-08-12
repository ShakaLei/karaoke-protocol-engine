#!/usr/bin/env python3
"""Batch runner — process every file in a drop-hub inbox through all stations, deliver to ready/.

SANITIZED FOR PUBLIC RELEASE: configure via environment variables.
  KPROT_HUB      — base URL of your drop hub (a small Cloudflare Worker + R2 inbox)
  KPROT_KEY_PATH — path to a file containing the hub's agent bearer key
  KARAOK_HOME    — directory containing the station scripts (default: this dir)
  VENV_PY        — python with faster-whisper/librosa installed (default: sys.executable)
"""
import os, sys, json, subprocess, urllib.request, urllib.parse
V = os.environ.get('VENV_PY', sys.executable)
K = os.environ.get('KARAOK_HOME', os.path.dirname(os.path.abspath(__file__)))
HUB = os.environ.get('KPROT_HUB', 'https://your-drop-hub.example.com')
KEY = open(os.environ.get('KPROT_KEY_PATH', './.agent-key')).read().strip()
os.environ.setdefault('TMPDIR', '/tmp')

def api(path, data=None, raw=False):
    req = urllib.request.Request(HUB + path, data=data,
        headers={'authorization': 'Bearer ' + KEY, 'user-agent': 'KPROT-batch/1.0'})
    r = urllib.request.urlopen(req)
    return r.read() if raw else json.load(r)

inbox = api('/agent/inbox')['items']
if not inbox:
    print('inbox empty — all quiet 🎤'); sys.exit(0)
os.chdir(K)
for it in inbox:
    key = it['key']; name = key.split('/', 1)[1]
    import re as _re
    base = _re.sub(r'^\d+-', '', name.rsplit('.', 1)[0])
    print('RUN', name, flush=True)
    try:
        audio = api('/agent/take?key=' + urllib.parse.quote(key), raw=True)
        open('batch-in.bin', 'wb').write(audio)
        subprocess.run(['ffmpeg', '-y', '-v', 'quiet', '-i', 'batch-in.bin', '-vn', '-ac', '1', '-ar', '22050', '-b:a', '96k', 'batch-audio.mp3'], check=True)
        subprocess.run([V, 'listen.py', 'batch-audio.mp3', 'batch-words.json'], check=True)
        subprocess.run([V, 'hear.py', 'batch-audio.mp3', 'batch-chords.json'], check=True)
        subprocess.run([V, 'weave.py', 'batch-words.json', 'batch-chords.json', 'batch-song.json'], check=True)
        subprocess.run([V, 'ignite.py', 'batch-song.json', 'batch-audio.mp3', base, f'{base}-karaoke.html'], check=True)
        subprocess.run([V, 'print.py', 'batch-song.json', base, 'the karaoke protocol', f'{base}-karaoke.pdf'], check=True)
        subprocess.run([V, 'make_mp4.py', 'batch-song.json', 'batch-audio.mp3', base, f'{base}-karaoke.mp4'], check=True)
        for f in [f'{base}-karaoke.html', f'{base}-karaoke.pdf', f'{base}-karaoke.mp4']:
            api('/agent/deliver?name=' + urllib.parse.quote(f), data=open(f, 'rb').read())
            print('  delivered', f, flush=True)
        api('/agent/complete?key=' + urllib.parse.quote(key), data=b'{}')
        print('DONE', name, flush=True)
    except Exception as e:
        print('FAIL', name, repr(e), flush=True)
