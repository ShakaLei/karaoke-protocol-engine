"""STATION 6 · BROADCAST — song.json + audio → karaoke MP4 (flames, word highlight, chords)
Renders frames with Pillow, muxes audio with ffmpeg. 1280x720 @ 24fps.
Usage: TMPDIR=/workspace/tmp python make_mp4.py song.json audio.mp3 "Title" out.mp4
"""
import sys, json, os, math, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

song_f, audio_f, title, out_f = sys.argv[1:5]
FPS, W, H = 24, 1280, 720
song = json.load(open(song_f))
lines = song["lines"]

# fonts
FD = "/usr/share/fonts/truetype/dejavu"
F_WORDS  = ImageFont.truetype(f"{FD}/DejaVuSans-Bold.ttf", 56)
F_WORDS2 = ImageFont.truetype(f"{FD}/DejaVuSans-Bold.ttf", 44)
F_CHORD  = ImageFont.truetype(f"{FD}/DejaVuSans-Bold.ttf", 30)
F_TITLE  = ImageFont.truetype(f"{FD}/DejaVuSans-Bold.ttf", 40)
F_SMALL  = ImageFont.truetype(f"{FD}/DejaVuSans.ttf", 22)

BG_TOP, BG_BOT = (11,7,16), (43,10,46)
GOLD  = (255,210,63)
FIRE  = (255,45,85)
ORANGE= (255,106,0)
INK   = (245,239,230)
DIM   = (120,108,140)

def bg_frame():
    im = Image.new("RGB", (W, H))
    dr = ImageDraw.Draw(im)
    for y in range(H):
        f = y / H
        c = tuple(int(BG_TOP[i] + (BG_BOT[i]-BG_TOP[i]) * f*f) for i in range(3))
        dr.line([(0,y),(W,y)], fill=c)
    return im
BG = bg_frame()

def flames_layer(cx, cy, w, h, t, seed):
    """a flickering flame blob behind a word"""
    layer = Image.new("RGBA", (w, h), (0,0,0,0))
    d = ImageDraw.Draw(layer)
    n = 7
    for i in range(n):
        f = i/(n-1)
        r = (1-f*0.75) * (min(w,h)/2)
        wig = math.sin(t*9 + i*1.7 + seed) * r*0.12
        col = [GOLD, ORANGE, FIRE][min(2, int(f*3))]
        alpha = int(190 * (1-f*0.8))
        d.ellipse([w/2-r+wig, h-r*1.4-f*6, w/2+r+wig, h*(1-f*0.12)], fill=col+(alpha,))
    return layer.filter(ImageFilter.GaussianBlur(6))

def draw_centered(draw, text, font, y, fill, stroke=0, stroke_fill=(0,0,0)):
    box = draw.textbbox((0,0), text, font=font, stroke_width=stroke)
    x = (W - (box[2]-box[0]))/2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)

def line_state(t):
    """current line + word states at time t"""
    for ln in lines:
        if ln["t0"]-0.05 <= t <= ln["t1"]+0.5:
            return ln, [(w["w"], w["t0"], w["t1"]) for w in ln["words"]]
    return None, None

def next_line(t):
    for ln in lines:
        if ln["t0"] > t: return ln
    return None

def render_frame(t):
    im = BG.copy().convert("RGBA")
    d = ImageDraw.Draw(im)
    d.text((30, 22), title, font=F_SMALL, fill=DIM)
    d.text((W-330, 22), "THE KARAOKE PROTOCOL", font=F_SMALL, fill=DIM)
    ln, words = line_state(t)
    if ln:
        if ln.get("chord"):
            box = d.textbbox((0,0), ln["chord"], font=F_CHORD)
            d.text(((W-(box[2]-box[0]))/2, 150), ln["chord"], font=F_CHORD, fill=GOLD)
        # sequential layout: assign each word a row/x ONCE
        n_words = len(words)
        total_chars = sum(len(w[0]) for w in words)
        font = F_WORDS if total_chars < 60 else (F_WORDS2 if total_chars < 110 else ImageFont.truetype(F_WORDS2.path, 34))
        space = d.textlength(" ", font=font)
        maxw = W - 160
        rows, cur, x = [], [], 0
        for wtxt, t0, t1 in words:
            ww = d.textlength(wtxt, font=font)
            if x + ww > maxw and cur:
                rows.append(cur); cur, x = [], 0
            cur.append((wtxt, t0, t1, x, ww)); x += ww + space
        if cur: rows.append(cur)
        # vertical centering around stage middle
        block_h = len(rows) * (font.size + 16)
        y0 = 200 + max(0, (380 - block_h)) // 2 + 60
        for ri, row in enumerate(rows):
            row_w = row[-1][3] + row[-1][4]
            xoff = (W - row_w) / 2
            y = y0 + ri * (font.size + 16)
            for wtxt, t0, t1, wx, ww in row:
                x = xoff + wx
                if t0 <= t < t1:
                    fl = flames_layer(int(x+ww/2), y, int(ww)+80, 140, t, hash(wtxt)%10)
                    im.alpha_composite(fl, (int(x-40), int(y-80)))
                    d.text((x, y), wtxt, font=font, fill=(255,255,255), stroke_width=2, stroke_fill=FIRE)
                elif t >= t1:
                    d.text((x, y), wtxt, font=font, fill=GOLD)
                else:
                    d.text((x, y), wtxt, font=font, fill=INK)
    else:
        nxt = next_line(t)
        msg = title if lines and t < lines[0]["t0"] else "\u266a"
        draw_centered(d, msg, F_TITLE, 320, DIM)
    dur = max(l["t1"] for l in lines) + 2
    d.rounded_rectangle([60, H-50, W-60, H-38], 6, fill=(255,255,255,28))
    d.rounded_rectangle([60, H-50, 60 + (W-120)*min(1,t/dur), H-38], 6, fill=GOLD)
    return im.convert("RGB")

# duration = audio duration
dur = float(subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",audio_f],
            capture_output=True, text=True).stdout.strip())
tmp = tempfile.mkdtemp(dir="/workspace/tmp")
n = int(dur*FPS)
print(f"rendering {n} frames ({dur:.1f}s @ {FPS}fps)…", flush=True)
for i in range(n):
    render_frame(i/FPS).save(f"{tmp}/f{i:06d}.png")
    if i % (FPS*10) == 0: print(f"  {i}/{n}", flush=True)
subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",f"{tmp}/f%06d.png","-i",audio_f,
                "-c:v","libx264","-pix_fmt","yuv420p","-crf","23","-c:a","aac","-b:a","128k",
                "-shortest", out_f], check=True, capture_output=True)
shutil.rmtree(tmp)
print(f"BROADCAST ✓ karaoke mp4 → {out_f} ({os.path.getsize(out_f)//1024} KB)")
