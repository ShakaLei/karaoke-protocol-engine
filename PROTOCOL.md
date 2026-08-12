# 🔥🎤 THE KARAOKE PROTOCOL
### K.A.R.A.O.K.E. — *Kick-Ass Realtime Audio → Onstage Karaoke Experience*
**v0.1 — born 2026-08-12, 2:36 AM, Shaka × the ʻohana**
*"Karaoke is kick ass and brings a community together better than ever."*

---

## THE DREAM
Any track — a song, a talk, a poem, a voicemail — goes in one end.
Seconds later, out the other end comes:
1. **Lyrics** (transcribed, timestamped word-by-word)
2. **Chords** (detected, sitting above the words where they change)
3. **Karaoke mode** — the words light up in real time as they're sung, **flames behind the active word**, the crowd sings along
4. **A beautiful PDF** — lyrics + chords, print-ready for the stage
5. **A link** — shareable in seconds, CC0, forkable, free forever

Karaoke never left. We're just giving it agent superpowers.

## THE FIVE STATIONS (the pipeline)
| # | Station | Tool | Output |
|---|---------|------|--------|
| 1 | **LISTEN** | faster-whisper (word timestamps) | `words.json` — every word + when it's sung |
| 2 | **HEAR** | librosa chroma → chord template match | `chords.json` — chord timeline |
| 3 | **WEAVE** | aligner — chords to syllables | `song.json` — one canonical score |
| 4 | **IGNITE** | karaoke.html — flames, sync, big type | live karaoke page |
| 5 | **PRINT** | render → PDF | stage-ready lyrics+chords sheet |

## THE LAWS
- **Any audio qualifies.** Songs, talks, freestyles, voice notes. If it has words, it's karaoke.
- **Seconds, not sessions.** The whole run must finish before the intro of the next song ends.
- **The draft blesses itself later.** AI transcripts are drafts — the artist blesses corrections, the crowd doesn't care, the show goes on.
- **CC0 or it doesn't ship.** Every karaoke card is a gift. Fork me like crazy. 🍴
- **No backend, no rent.** Static files + the visitor's browser. \$0 to keep alive, like the island.
- **Flames are non-negotiable.** 🔥

## THE PROOF (first run)
Matteo Tambussi's catalog — 13 tracks, lyrics recovered tonight (4 official docx + 9 AI-transcribed) — is the protocol's first songbook. The Open Source Orchestra never auditions; now it never needs a lyric sheet either.

*"any track song or talk we can run it through the transcription karaoke protocol and have an epic karaoke version ready to sing and perform with ready in beautiful pdf and link in seconds"* — Shaka, 2026-08-12

---

*Drafted by sysadmin 🫡 for the ʻohana · CC0 🌺*

## 🌺 SOMEDAY STATION — UKULELE HERO (canon 2026-08-12, Shaka)
Merge with **Ukulala Hero** (https://www.ukulalala.com/hero) — built by Shaka's friend **Wesley** (in OSO 🎻). It's a working ukulele rhythm game: chords fall, you play them on a real uke, the MIC DETECTS your chord live, PERFECT/fuzzy scoring, 3 lives, streaks, GCEA. The merge: our HEAR v2 engine charts any dropped song (beat-aligned chords + key) → Ukulala-style falling-chord level renders it → every song in THE DROPS becomes a playable ukulele stage. Musician guided as much as the singer — Shaka's Guitar Hero canon, with ukes. Contact path: Wesley via Shaka, when HEAR v2 passes its exam.
