"""STATION 2 · HEAR v2 — musician-grade chord engine for THE KARAOKE PROTOCOL.
Pipeline: demucs separation (6-stem default) -> BTC-ISMIR19 Bi-Directional Transformer
          chord recognition on TWO stem mixes (harmony base + guitar/piano color stem)
          -> chart-aware merge (roots from base, extensions from color stem)
          -> Krumhansl-Schmuckler key reader -> chords2.json (weave-compatible)
usage: hear2.py in.mp3 out.json [--stem mix|harmony] [--no-separate] [--no-refine]
                                [--model htdemucs_6s|htdemucs] [--min-seg SECONDS]
"""
import os, sys, json, argparse
os.environ.setdefault("TMPDIR", "/workspace/tmp")
os.environ.setdefault("TORCH_HOME", "/workspace/.torch")
os.environ.setdefault("HF_HOME", "/workspace/.hf-demucs-models")  # keep demucs models OFF the tiny overlay
import numpy as np

BTC_DIR = "/workspace/btc"
sys.path.insert(0, BTC_DIR)

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
PLAIN = {"", "m"}  # plain qualities eligible for extension refinement


def separate(audio_path, model_name="htdemucs_6s"):
    """demucs -> {stem_name: mono np.array}, sample_rate"""
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    from demucs.audio import AudioFile
    model = get_model(model_name)
    model.eval()
    wav = AudioFile(audio_path).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / (ref.std() + 1e-8)
    with torch.no_grad():
        sources = apply_model(model, wav[None], device="cpu", shifts=0, split=True, overlap=0.25, progress=False)[0]
    sources = sources * ref.std() + ref.mean()
    return {n: sources[i].mean(0).cpu().numpy() for i, n in enumerate(model.sources)}, model.samplerate


def write_mix(stems, keep, sr, tag):
    import soundfile as sf
    mix = None
    for s in keep:
        if s in stems:
            mix = stems[s].copy() if mix is None else mix + stems[s]
    if mix is None:
        return None
    out = os.path.join(os.environ["TMPDIR"], f"hear2-{tag}.wav")
    sf.write(out, mix.astype(np.float32), sr)
    return out


def monoize(path):
    """BTC/librosa fold stereo to mono by AVERAGING — deadly for center-cut side-only
    instrumentals (L-R, R-L cancel to silence). Pick the loudest channel instead."""
    import librosa, soundfile as sf
    y, sr = librosa.load(path, sr=22050, mono=False)
    if y.ndim == 1:
        return path
    rms = np.sqrt((y ** 2).mean(axis=1))
    avg = np.sqrt((y.mean(axis=0) ** 2).mean())
    if avg > 0.5 * rms.max():
        return path  # normal stereo, fold-down safe
    out = os.path.join(os.environ["TMPDIR"], "hear2-mono.wav")
    sf.write(out, y[int(np.argmax(rms))], sr)
    print(f"HEAR2 · side-only stereo detected (fold-down would silence) — using channel {int(np.argmax(rms))}", flush=True)
    return out


def btc_chords(audio_path):
    """BTC-ISMIR19 large-voca inference -> list of (t0, t1, chord_label like 'C:maj7')"""
    import torch
    from btc_model import BTC_model
    from utils.hparams import HParams
    from utils.mir_eval_modules import audio_file_to_features, idx2voca_chord
    config = HParams.load(os.path.join(BTC_DIR, "run_config.yaml"))
    config.feature["large_voca"] = True
    config.model["num_chords"] = 170
    idx_to_chord = idx2voca_chord()
    model = BTC_model(config=config.model).to("cpu")
    checkpoint = torch.load(os.path.join(BTC_DIR, "test/btc_model_large_voca.pt"),
                            map_location="cpu", weights_only=False)
    mean, std = checkpoint["mean"], checkpoint["std"]
    model.load_state_dict(checkpoint["model"])
    model.eval()
    feature, feature_per_second, _ = audio_file_to_features(audio_path, config)
    feature = (feature.T - mean) / std
    time_unit = feature_per_second
    n_timestep = config.model["timestep"]
    num_pad = n_timestep - (feature.shape[0] % n_timestep)
    feature = np.pad(feature, ((0, num_pad), (0, 0)), mode="constant", constant_values=0)
    num_instance = feature.shape[0] // n_timestep
    segs, start_time, prev = [], 0.0, None
    with torch.no_grad():
        feat = torch.tensor(feature, dtype=torch.float32).unsqueeze(0)
        for t in range(num_instance):
            attn, _ = model.self_attn_layers(feat[:, n_timestep * t:n_timestep * (t + 1), :])
            pred, _ = model.output_layer(attn)
            pred = pred.squeeze()
            for i in range(n_timestep):
                cur_t = time_unit * (n_timestep * t + i)
                if prev is None:
                    prev = pred[i].item(); continue
                if pred[i].item() != prev:
                    segs.append((start_time, cur_t, idx_to_chord[prev]))
                    start_time = cur_t
                    prev = pred[i].item()
                if t == num_instance - 1 and i + num_pad == n_timestep:
                    if start_time != cur_t:
                        segs.append((start_time, cur_t, idx_to_chord[prev]))
                    break
    return segs


def pretty(label):
    """BTC label -> guitar-hero style: 'C:maj7'->'Cmaj7', 'C:min'->'Cm', 'F'->'F'"""
    if label in ("N", "X"):
        return "N"
    if ":" not in label:
        return label
    root, q = label.split(":", 1)
    qmap = {"maj": "", "min": "m", "dim": "dim", "aug": "aug", "min6": "m6", "maj6": "6",
            "min7": "m7", "minmaj7": "m(maj7)", "maj7": "maj7", "7": "7", "dim7": "dim7",
            "hdim7": "m7b5", "sus2": "sus2", "sus4": "sus4"}
    return root + qmap.get(q, q)


def parse(chord):
    """'Cmaj7'->('C','maj7'), 'F#m7'->('F#','m7'), 'F'->('F',''), 'N'->('N','')"""
    if chord == "N":
        return "N", ""
    root = chord[:2] if len(chord) > 1 and chord[1] == "#" else chord[:1]
    return root, chord[len(root):]


def smooth(segs, min_seg=0.8):
    """Absorb segments shorter than min_seg seconds into the longer neighbor (iterative)."""
    segs = [list(s) for s in segs]
    changed = True
    while changed and len(segs) > 1:
        changed = False
        for i, s in enumerate(segs):
            if s[1] - s[0] < min_seg:
                left = segs[i - 1] if i > 0 else None
                right = segs[i + 1] if i + 1 < len(segs) else None
                if left is None:
                    right[0] = s[0]
                elif right is None:
                    left[1] = s[1]
                elif (left[1] - left[0]) >= (right[1] - right[0]):
                    left[1] = s[1]
                else:
                    right[0] = s[0]
                segs.pop(i)
                changed = True
                break
    return segs


def merge_consecutive(segs):
    chords = []
    for t0, t1, c in segs:
        if chords and chords[-1]["c"] == c:
            chords[-1]["t1"] = round(float(t1), 2)
        else:
            chords.append({"c": c, "t0": round(float(t0), 2), "t1": round(float(t1), 2)})
    return chords


def refine_extensions(base_segs, color_segs):
    """Chart-aware merge: base timeline has the roots; color stem (guitar+piano) has the
    voicings. Where color stem says same-root + extended quality, adopt it.
    - color seg fully inside a plain base seg (>=1.0s)  -> split base, insert extension
    - same-root extended color coverage >= 35% of base  -> relabel whole base seg
    """
    out = []
    for bt0, bt1, bc in base_segs:
        broot, bqual = parse(bc)
        if bc == "N" or bqual not in PLAIN or (bt1 - bt0) < 1.5:
            out.append((bt0, bt1, bc)); continue
        cands = []
        for ct0, ct1, cc in color_segs:
            croot, cqual = parse(cc)
            if croot != broot or cqual in PLAIN or cqual == "":
                continue
            ov = min(bt1, ct1) - max(bt0, ct0)
            if ov >= 0.5:
                cands.append((ct0, ct1, cc, ov))
        if not cands:
            out.append((bt0, bt1, bc)); continue
        total_ov = sum(c[3] for c in cands)
        best = max(cands, key=lambda c: c[3])
        if total_ov >= 0.35 * (bt1 - bt0):
            out.append((bt0, bt1, best[2])); continue
        if best[0] >= bt0 and best[1] <= bt1 and (best[1] - best[0]) >= 1.0:
            if best[0] - bt0 >= 0.5:
                out.append((bt0, best[0], bc))
            out.append((max(bt0, best[0]), min(bt1, best[1]), best[2]))
            if bt1 - best[1] >= 0.5:
                out.append((best[1], bt1, bc))
            continue
        out.append((bt0, bt1, bc))
    return out


def key_ks(y, sr, hop=2048):
    """Krumhansl-Schmuckler key reader on mean CQT chroma -> (key, mode, correlation)."""
    import librosa
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop).mean(axis=1)
    chroma = chroma / (chroma.sum() + 1e-9)
    maj = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    mnr = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    best, bs = None, -2
    for i in range(12):
        for prof, mode in ((maj, "major"), (mnr, "minor")):
            r = float(np.corrcoef(np.roll(prof, i), chroma)[0, 1])
            if r > bs:
                bs, best = r, (NOTES[i], mode)
    return best[0], best[1], round(bs, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--no-separate", action="store_true", help="skip demucs (input already separated)")
    ap.add_argument("--stem", default="auto", choices=["auto", "mix"],
                    help="mix = run BTC on the full mix, no separation")
    ap.add_argument("--model", default="htdemucs_6s", help="demucs model (htdemucs_6s | htdemucs)")
    ap.add_argument("--no-refine", action="store_true", help="skip color-stem extension refinement")
    ap.add_argument("--min-seg", type=float, default=0.8)
    ap.add_argument("--instrumental", metavar="OUT.mp3",
                    help="also write a demucs no-vocals instrumental (free: separation already done)")
    args = ap.parse_args()

    six_stem = "6s" in args.model
    if args.stem == "mix" or args.no_separate:
        base_src = monoize(args.src)
        color_src, bpm_src, key_src = None, base_src, base_src
        tag = "input-as-is"
    else:
        print(f"HEAR2 · demucs {args.model} separating...", flush=True)
        stems, ssr = separate(args.src, args.model)
        keep_base = [s for s in ("bass", "other", "guitar", "piano") if s in stems]
        base_src = write_mix(stems, keep_base, ssr, "base")
        color_src = None
        if six_stem and not args.no_refine:
            color_src = write_mix(stems, ("guitar", "piano"), ssr, "color")
        bpm_src = monoize(args.src)  # beat-track the ORIGINAL (real drums > separated bleed)
        key_src = base_src
        if args.instrumental:
            import soundfile as sf, subprocess as _sp
            keep_inst = [s for s in stems if s != "vocals"]
            mix = None
            for s in keep_inst:
                mix = stems[s].copy() if mix is None else mix + stems[s]
            wav_out = os.path.join(os.environ["TMPDIR"], "hear2-instrumental.wav")
            sf.write(wav_out, mix.astype(np.float32), ssr)
            _sp.run(["ffmpeg", "-y", "-v", "quiet", "-i", wav_out, "-b:a", "160k", args.instrumental], check=True)
            os.remove(wav_out)
            print(f"HEAR2 · instrumental ({'+'.join(keep_inst)}) → {args.instrumental}", flush=True)
        tag = f"{args.model}:{'+'.join(keep_base)}"
        print(f"HEAR2 · stems -> base({'+'.join(keep_base)})" + (" + color(guitar+piano)" if color_src else ""), flush=True)

    print("HEAR2 · BTC transformer charting (base)...", flush=True)
    base = smooth([(a, b, pretty(c)) for a, b, c in btc_chords(base_src)], args.min_seg)
    refined = base
    if color_src:
        print("HEAR2 · BTC transformer charting (color stem)...", flush=True)
        color = smooth([(a, b, pretty(c)) for a, b, c in btc_chords(color_src)], args.min_seg)
        refined = refine_extensions(base, color)
        n_ext = sum(1 for a, b, c in refined if parse(c)[1] not in PLAIN and c != "N")
        print(f"HEAR2 · refinement: {n_ext} extended-quality segments adopted from color stem", flush=True)
    chords = merge_consecutive(smooth(refined, 0.5))

    import librosa
    y, sr = librosa.load(key_src, sr=22050, mono=True)
    key, mode, corr = key_ks(y, sr)
    yb, srb = librosa.load(bpm_src, sr=22050, mono=True)
    tempo, _ = librosa.beat.beat_track(y=yb, sr=srb, hop_length=2048)
    bpm = round(float(np.atleast_1d(tempo)[0]), 1)

    payload = {
        "key": key, "mode": mode, "key_confidence": corr, "bpm": bpm,
        "engine": "demucs + BTC-ISMIR19(large-voca) + color-stem refinement + Krumhansl-Schmuckler",
        "source_stem": tag,
        "chords": chords,  # weave-compatible canonical
        "segments": [{"t0": c["t0"], "t1": c["t1"], "chord": c["c"]} for c in chords],
    }
    json.dump(payload, open(args.out, "w"))
    print(f"HEAR2 ✓ key {key} {mode} (r={corr}) · bpm {bpm} · {len(chords)} segments → {args.out}", flush=True)
    for c in chords:
        print(f"  {c['t0']:8.2f} – {c['t1']:8.2f}  {c['c']}", flush=True)


if __name__ == "__main__":
    main()
