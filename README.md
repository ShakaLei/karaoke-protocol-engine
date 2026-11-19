# 🔥🎤 karaoke-protocol-engine

**Any track → 7 stations → a karaoke pack (live HTML + stage PDF + MP4) in seconds.**

This is the engine behind [THE KARAOKE PROTOCOL](PROTOCOL.md) — *K.A.R.A.O.K.E. = Kick-Ass Realtime Audio → Onstage Karaoke Experience*. Born 2026-08-12 at 2:36 AM in the ShakaVerse, built by Shaka Lei Kaumaka × his AI ʻohana (115+ agents), shipped the same hour. Now CC BY-SA 4.0 — fork me like crazy. 🍴

> *"any track song or talk we can run it through the transcription karaoke protocol and have an epic karaoke version ready to sing and perform with ready in beautiful pdf and link in seconds"* — Shaka

## The 7 stations

| # | Station | Script | What it does |
|---|---------|--------|--------------|
| 1 | **LISTEN** | `listen.py` | faster-whisper word-level transcription → `words.json` (every word + when it's sung) |
| 2 | **HEAR** | `hear.py` | librosa chroma → maj/min chord template match → `chords.json` |
| 2+ | **HEAR v2** | `hear2.py` | musician-grade engine: demucs stem separation → BTC-ISMIR19 transformer chord recognition on two stem mixes → Krumhansl-Schmuckler key reader → `chords2.json` |
| 3 | **WEAVE** | `weave.py` | aligns words + chords into one canonical score → `song.json` |
| 4 | **IGNITE** | `ignite.py` | `song.json` + audio → self-contained karaoke HTML: words light up in real time, **flames behind the active word** 🔥, chords above the lines |
| 5 | **PRINT** | `print.py` | `song.json` → stage-ready lyrics+chords PDF (headless Chromium) |
| 6 | **BROADCAST** | `make_mp4.py` | `song.json` + audio → 720p karaoke MP4 (Pillow frames + ffmpeg) |
| 7 | **MUTE** | `mute.sh` | center-channel vocal cut → instrumental (demucs = the v2 upgrade path) |

`batch.py` = the unattended runner: pulls audio from a drop-hub inbox, runs every station, delivers the pack back. (Sanitized for release — configure via env vars.)

## Quick start

```bash
pip install faster-whisper librosa numpy pillow soundfile
# for hear2.py also: torch, demucs, and the BTC-ISMIR19 chord model
export TMPDIR=/some/big/disk/tmp   # ⚠️ THE TMPDIR LAW — see below

python listen.py song.mp3 words.json
python hear2.py  song.mp3 chords2.json        # or hear.py for the lite path
python weave.py  words.json chords2.json song.json
python ignite.py song.json song.mp3 "My Song" my-song-karaoke.html
python print.py  song.json "My Song" "the karaoke protocol" my-song-karaoke.pdf
python make_mp4.py song.json song.mp3 "My Song" my-song-karaoke.mp4
./mute.sh song.mp3 song-instrumental.mp3
```

Outputs are static files — **no backend, no rent**. Host the HTML anywhere; the flames run in the visitor's browser at $0.

## The exam where the machine learned Cmaj7 from the artist's ear 🎓

HEAR v1 (template matching) could only hear plain major/minor. The artist (Matteo Tambussi) heard a **Cmaj7** where the machine heard C. So we sat the machine down for an exam — the full story is in [HEAR2-EXAM-REPORT.md](HEAR2-EXAM-REPORT.md):

- **demucs** separates the track into stems (bass/drums/other/vocals/guitar/piano).
- **BTC-ISMIR19** (Bi-Directional Transformer for Chord Recognition, ISMIR 2019) charts **two stem mixes**: a *harmony base* mix for roots, and a *guitar/piano color* mix for extensions.
- A chart-aware merge takes **roots from the base** and **7ths/9ths/extensions from the color stem**.
- **Krumhansl-Schmuckler** reads the key (C major, r=0.871) off the base-stem chroma.

**Verdict: EXAM PASS** — roots 100% exact, Cmaj7 color detected in every strongly-voiced cycle. The machine learned to hear the maj7 the artist's ear insisted was there. *The draft blesses itself later; the artist blesses the draft.*

## The TMPDIR law ⚠️

Whisper models, demucs models, torch caches and intermediate WAVs are **gigabytes**. If your root filesystem is a small overlay (hello, containers), everything silently fills it and dies weird deaths. The law:

```bash
export TMPDIR=/path/to/big/disk/tmp
export HF_HOME=/path/to/big/disk/hf
export TORCH_HOME=/path/to/big/disk/torch
```

Point every cache at the big disk *before* you run anything. We learned this at 3 AM so you don't have to.

## The laws of the protocol

- **Any audio qualifies.** Songs, talks, freestyles, voice notes. If it has words, it's karaoke.
- **Seconds, not sessions.** The whole run must finish before the intro of the next song ends.
- **The draft blesses itself later.** AI transcripts are drafts — the artist blesses corrections, the crowd doesn't care, the show goes on.
- **Copyleft or it doesn't ship.** Every karaoke card is a gift.
- **No backend, no rent.** Static files + the visitor's browser.
- **Flames are non-negotiable.** 🔥

## Provenance

First full run: Matteo Tambussi's *"Be My Friend"* — all stations, flames karaoke HTML + chords PDF, QA'd, in the first hour of the protocol's life. Matteo's 13-track catalog is the protocol's first songbook. The front door is [karaokeprotocol.com](https://karaokeprotocol.com).

CC BY-SA 4.0 🌺 gifted with love & aloha by Shaka Lei Kaumaka & the ʻohana — see [GIFT.md](GIFT.md) and [LICENSE](LICENSE).

## License

Code: GPL-3.0 (see LICENSE). Songs, lyrics, chords, words, art, links and pages: CC BY-SA 4.0 (see LICENSE-CONTENT). Credit: Shaka Lei Kaumaka and the ʻohana. CC0 is retired — copyleft now guards the gift as of 19 Nov 2026; versions published earlier under CC0 stay CC0.

Earlier license note (before 19 Nov 2026; any third-party rights or carve-outs in it still apply):

> Code in this repository is licensed **GPL-3.0-or-later** (copyleft — share-alike for code); see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
> Words, art, songs and data: **CC BY-SA 4.0** since 19 Nov 2026 / their makers' own terms. Everything published before 2026-10-29 stays under its old licence, irrevocably.
> By the ʻohana — Shaka's AI family.
