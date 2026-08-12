#!/bin/bash
# STATION 7 · MUTE (lite) — center-channel vocal cut: vocals are usually center-panned,
# so side = L-R removes them. demucs stem separation = v2 upgrade path.
# usage: mute.sh in.mp3 out-instrumental.mp3
ffmpeg -y -i "$1" -af "pan=stereo|c0=c0-c1|c1=c1-c0,highpass=f=80" -b:a 160k "$2"
echo "MUTE ✓ instrumental → $2"
