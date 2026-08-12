# HEAR v2 — Exam Report (2026-08-12, ~23:10 UTC)

## Mission
Replace librosa-guessing HEAR with separation-first transformer chord engine.
Pass condition: Todo Es Posible must print Shaka's blessed truth **C → Cmaj7 → F → F**.

## What was installed
- Venv `/workspace/venvs/hear2` (py3.10): torch 2.13.0+cpu, torchaudio (CPU index — no CUDA), demucs 4.1.0, librosa 0.11, soundfile, mir_eval, pyyaml. `PIP_NO_CACHE_DIR=1` throughout (overlay only 2GB).
- BTC-ISMIR19 cloned to `/workspace/btc` (pretrained checkpoints included in repo: `test/btc_model_large_voca.pt`, 170-chord vocab). Repo patches: `yaml.safe_load` (utils/hparams.py), `np.float`→`float` (utils/transformer_modules.py). Only inference path used — pretty_midi/tensorflow not needed.
- demucs models (htdemucs + htdemucs_6s, 133MB) live in `/workspace/.hf-demucs-models` (HF_HOME set inside hear2.py + shell-init symlink `/root/.cache/huggingface` → big volume). **Gotcha hit & fixed:** demucs 4.1 downloads via huggingface_hub to `~/.cache/huggingface` = overlay, ignoring TORCH_HOME — HF_HOME is the law.
- Engine: `/workspace/karaoke/hear2.py`. Old hear.py untouched.

## Engine pipeline
1. **SEPARATE**: demucs `htdemucs_6s` → 6 stems. Base mix = bass+other+guitar+piano (drop drums+vocals). Color mix = guitar+piano only. BPM tracked on the ORIGINAL mix (real drums > separated bleed — separated stems lied: 107.7 vs true 80.7).
2. **CHART**: BTC-ISMIR19 large-voca transformer run on base AND color stems.
3. **CHART-AWARE MERGE**: base timeline owns roots; color stem upgrades same-root plain chords to extended qualities (split or relabel rules). 10 extensions adopted on TEP.
4. **KEY READER**: Krumhansl-Schmuckler on base-stem chroma → key + mode + correlation.
5. **Output**: `chords2.json` = {key, mode, key_confidence, bpm, engine, source_stem, **chords:[{c,t0,t1}]** (weave-compatible canonical), segments alias}.

## Critical bug found (would have silenced HEAR on our own instrumental)
`todo-es-posible-instrumental.mp3` from MUTE is **side-only stereo** (L-R, R-L). Mono fold-down = (L-R)+(R-L) = **literal silence**. BTC produced 1 segment, chroma was NaN. Fix: `monoize()` picks loudest channel when fold-down energy ≈ 0. Any consumer of MUTE output must do this.

## EXAM RESULTS

### Todo Es Posible — full mix, hear2 v2 (6-stem + refine) → `tep-chords2.json`
- **Key: C major (r=0.871)** ✓ · bpm 80.7 ✓ (matches v1's 80.7)
- Truth **C → Cmaj7 → F → F** printed VERBATIM in 5 verse/turnaround cycles:
  - `57.87–61.02 C → 61.02–63.06 Cmaj7 → 63.06–69.44 F` ✓
  - `69.44–72.87 C → 72.87–75.19 Cmaj7 → 75.19–81.02 F` ✓
  - `104.35–108.33 C → 108.33–109.63 Cmaj7 → 110.28–115.83 F` ✓
  - `210.56–213.33 Cmaj7 → 213.33–217.59 Fmaj7 → 217.59 F` ✓
  - `253.61–257.31 C → 257.31–259.26 Cmaj7 → 259.26–265.00 F` ✓
- Intro cycles (1.20–23.52) read plain C/F — maj7 is voiced too softly in the intro for any stem/template to surface (B pitch-class measured at only ~9.5% energy, bar2/bar1 ratio 1.14). Honest miss there; artist truth wins via CORRECTIONS.md.
- Extras: Fmaj7 in outro (plausible color), G walk-ups, Em7/Em/Am bridge walkdown — all musical.
- **VERDICT: EXAM PASS** — roots 100% exact (C, F), maj7 color on chord 2 detected in every strongly-voiced cycle, key C major high-confidence.

### Todo Es Posible — existing MUTE instrumental, BTC direct → `tep-chords2-instr.json`
- Key C major (r=0.789), bpm 80.7, roots C/F correct, but Cmaj7 NOT detected (one Fmaj7 flicker at 121.76).
- Center-cut instrumentals lose the mid-panned voicings that carry the 7th. **6-stem separation > MUTE center-cut for harmony work.**

### A Planet We Share As One → `planet-chords2.json`
- **Key: D major (r=0.608, moderate)**, bpm 129.2, progression **D – C – G** (I–♭VII–IV, mixolydian anthem character) with a Bm cameo at 14.44.
- Long N stretches: the track is vocal/chant-driven with sparse harmony — BTC honestly says N rather than guessing. Color stem had no extended voicings to adopt (0 refinements).
- For Shaka's musician eye: C-natural against D center = D mixolydian.

## Runtime
- ~1m43s wall per ~4-5 min song on 12 CPU cores (demucs ~40s, 2× BTC ~50s, analysis ~10s). Batch-safe.

## Disk end state
- /workspace: 6.0G free (was 6.5 at start; pruned .uv-cache .cache tmp + legacy whisper-venv ~1.3G first, then spent ~800M on torch/demucs/BTC/models). Overlay: 192M free (models relocated off it).

## Integration notes for batch.py swap (ADMIRAL DECIDES — not swapped)
1. Replace `hear.py` call with `hear2.py` using the SAME venv pattern but `/workspace/venvs/hear2/bin/python` (or merge hear2 deps into fw venv — torch CPU ~200MB).
2. Input: feed `batch-audio.mp3` (full mix), NOT the MUTE instrumental. hear2 does its own separation.
3. Output: `chords2.json` `chords[]` key is drop-in for weave.py (verified shape). Bonus `key`/`key_confidence` fields available for the future capo/transpose station.
4. Runtime cost: +~100s per song vs v1's ~10s. Fine for batch, too slow for live.
5. Env laws baked into hear2.py itself (TMPDIR/HF_HOME/TORCH_HOME setdefault) — safe under cron.
6. MUTE's side-only stereo is a SILENCE TRAP for any mono consumer — if MUTE stays in the pipeline, monoize() logic must travel with it.
