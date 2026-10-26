#!/usr/bin/env python3
"""
Starforge-mobile — SFX batch (brief §2.4 / docs/ASSET_UI_SPEC.md §5).

Five procedurally synthesised game sounds. No samples, no licences, no cost:
every waveform is generated from scratch, so the assets are commercial-safe
and reproducible from source.

Specs (from docs/ASSET_UI_SPEC.md §5):
  Ogg Vorbis | 44100 Hz | mono (sting may be stereo) | peak -6 dBFS
  no DC offset | <=30 ms fade-out at the end | <=2 s per file

  sfx_deploy.ogg  <=0.6s  whoosh - downward sweep + landing impact
  sfx_hit.ogg     <=0.4s  thud  - low-frequency impact, short decay
  sfx_death.ogg   <=0.8s  zap   - noise + descending tone
  sfx_mineral.ogg <=0.5s  crisp rising chime (must cut through a battle mix)
  sfx_win.ogg     <=2.0s  rising chord / sting

Usage:
    python3 tools/sfx_generator.py [REPO_PATH]
"""
import math
import os
import random
import struct
import shutil
import subprocess
import sys
import wave

SR = 44100
PEAK = 10 ** (-6.0 / 20.0)          # -6 dBFS
FADE_MS = 30


# ---------------------------------------------------------------- helpers

def silence(dur):
    return [0.0] * int(SR * dur)


def sine(freq, dur, amp=1.0, phase=0.0):
    n = int(SR * dur)
    return [amp * math.sin(2 * math.pi * freq * i / SR + phase) for i in range(n)]


def sweep(f0, f1, dur, amp=1.0, wave_fn=math.sin):
    """Frequency sweep f0 -> f1 (linear), returns a list of samples."""
    n = int(SR * dur)
    out = []
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / max(n - 1, 1))
        ph += 2 * math.pi * f / SR
        out.append(amp * wave_fn(ph))
    return out


def square(ph):
    return 1.0 if math.sin(ph) >= 0 else -1.0


def saw(ph):
    return ((ph / math.pi) % 2.0) - 1.0


def noise(dur, amp=1.0, seed=1):
    rnd = random.Random(seed)
    return [amp * (rnd.random() * 2 - 1) for _ in range(int(SR * dur))]


def lowpass(sig, cutoff):
    """One-pole low-pass; cutoff may be a list (per-sample) or a float."""
    out = []
    y = 0.0
    for i, x in enumerate(sig):
        fc = cutoff[i] if isinstance(cutoff, list) else cutoff
        a = 1.0 - math.exp(-2.0 * math.pi * fc / SR)
        y += a * (x - y)
        out.append(y)
    return out


def highpass(sig, cutoff):
    lp = lowpass(sig, cutoff)
    return [x - y for x, y in zip(sig, lp)]


def mix(*layers):
    n = max(len(l) for l in layers)
    out = [0.0] * n
    for l in layers:
        for i, v in enumerate(l):
            out[i] += v
    return out


def at(offset, sig, total):
    """Place sig into a buffer of length total starting at offset."""
    buf = [0.0] * total
    for i, v in enumerate(sig):
        j = offset + i
        if 0 <= j < total:
            buf[j] += v
    return buf


def env_decay(sig, tau):
    return [v * math.exp(-i / (SR * tau)) for i, v in enumerate(sig)]


def env_attack_decay(sig, attack, decay):
    n = len(sig)
    a = max(int(SR * attack), 1)
    out = []
    for i, v in enumerate(sig):
        g = (i / a) if i < a else 1.0
        out.append(v * g * math.exp(-(i - a) / (SR * decay) if i >= a else 0.0))
    return out


def fade_out(sig, ms=FADE_MS):
    """Smooth fade to exact zero over the last `ms` (no end-of-file click)."""
    n = min(int(SR * ms / 1000), len(sig))
    if n <= 0:
        return sig
    out = list(sig)
    for i in range(n):
        k = (i + 1) / n
        out[len(sig) - n + i] *= k * k
    out[-1] = 0.0
    return out


def remove_dc(sig):
    if not sig:
        return sig
    mean = sum(sig) / len(sig)
    return [v - mean for v in sig]


def normalize(sig, peak=PEAK):
    m = max((abs(v) for v in sig), default=0.0)
    if m == 0:
        return sig
    g = peak / m
    return [v * g for v in sig]


def finish(sig):
    sig = remove_dc(sig)
    sig = normalize(sig)
    return fade_out(sig)


def write_wav(path, sig, channels=1):
    data = bytearray()
    for v in sig:
        s = int(max(-1.0, min(1.0, v)) * 32767)
        data += struct.pack('<h', s)
    with wave.open(path, 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(bytes(data))


def ogg_encoder_available():
    """Ogg Vorbis is optional: this box's ffmpeg has no libvorbis and its
    native vorbis encoder is stereo-only, so WAV is the default delivery
    format (brief §2.4 allows wav/ogg)."""
    for exe in ("/opt/homebrew/opt/libvorbis/bin/oggenc", "oggenc"):
        if shutil.which(exe):
            return exe
    return None


def to_ogg(wav_path, ogg_path, channels=1):
    """Encode to Ogg Vorbis with oggenc when it is available."""
    exe = ogg_encoder_available()
    if not exe:
        raise RuntimeError("oggenc not available")
    cmd = [exe, "-Q", "-q", "4", "-o", ogg_path, wav_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return "oggenc"


# ---------------------------------------------------------------- voices

def sfx_deploy():
    """Whoosh: noise through a downward-sweeping low-pass, plus a landing thud."""
    dur = 0.52
    n = int(SR * dur)
    cut = [6000 - 5200 * (i / max(n - 1, 1)) ** 1.6 for i in range(n)]
    nz = noise(dur, 1.0, seed=7)
    whoosh = lowpass(nz, cut)
    whoosh = highpass(whoosh, 300)
    whoosh = [v * (math.sin(math.pi * i / n) ** 1.5) for i, v in enumerate(whoosh)]
    # landing impact
    imp = env_decay(sweep(150, 60, 0.16), 0.055)
    imp = [v * 0.9 for v in imp]
    body = env_decay(sweep(70, 45, 0.2), 0.07)
    sig = mix(whoosh, at(int(SR * 0.33), imp, n), at(int(SR * 0.33), body, n))
    return finish(sig)


def sfx_hit():
    """Thud: low body thump + a short filtered transient."""
    dur = 0.30
    n = int(SR * dur)
    body = env_decay(sweep(130, 52, 0.24), 0.075)
    body = [v * 1.0 for v in body]
    click = lowpass(noise(0.03, 1.0, seed=3), 2200)
    click = env_decay(click, 0.012)
    sub = env_decay(sweep(60, 40, 0.2), 0.05)
    sig = mix(body, at(0, click, n), at(0, [v * 0.5 for v in sub], n))
    return finish(sig)


def sfx_death():
    """Zap: descending square + filtered noise crackle."""
    dur = 0.72
    n = int(SR * dur)
    tone = sweep(680, 130, 0.55, 1.0, wave_fn=square)
    tone = env_attack_decay(tone, 0.004, 0.20)
    tone = lowpass(tone, 3200)
    cr = highpass(noise(0.45, 0.8, seed=11), 1800)
    cr = env_attack_decay(cr, 0.002, 0.12)
    ring = env_decay(sweep(420, 300, 0.35), 0.11)
    sig = mix(tone, at(int(SR * 0.01), cr, n), at(int(SR * 0.02), ring, n))
    return finish(sig)


def sfx_mineral():
    """Crisp rising two-tone chime (must cut through a battle mix)."""
    dur = 0.42
    n = int(SR * dur)
    a = env_attack_decay(sine(880, 0.14, 0.7), 0.003, 0.045)
    a += [v * 0.35 for v in env_attack_decay(sine(1760, 0.14, 0.4), 0.003, 0.035)]
    b = env_attack_decay(sine(1318.5, 0.22, 0.8), 0.003, 0.075)
    b += [v * 0.3 for v in env_attack_decay(sine(2637, 0.22, 0.3), 0.003, 0.05)]
    spark = env_decay(highpass(noise(0.08, 0.35, seed=5), 4000), 0.02)
    sig = mix(a, at(int(SR * 0.13), b, n), at(0, spark, n))
    return finish(sig)


def sfx_win():
    """Sting: rising arpeggio into a sustained major chord (stereo)."""
    dur = 1.85
    n = int(SR * dur)
    notes = [(523.25, 0.00), (659.25, 0.16), (783.99, 0.32), (1046.50, 0.48)]
    arp = [0.0] * n
    for freq, off in notes:
        v = env_attack_decay(sine(freq, 0.34, 0.55), 0.004, 0.13)
        v += [x * 0.25 for x in env_attack_decay(sine(freq * 2, 0.34, 0.3), 0.004, 0.09)]
        v += [x * 0.12 for x in env_attack_decay(sine(freq * 3, 0.34, 0.2), 0.004, 0.06)]
        arp = mix(arp, at(int(SR * off), v, n))
    chord_notes = [(523.25, 0.0), (659.25, 0.0), (783.99, 0.0), (1046.50, 0.0)]
    pad_len = dur - 0.70
    pad = [0.0] * int(SR * pad_len)
    for freq, _ in chord_notes:
        pad = mix(pad, [v * 0.22 for v in env_attack_decay(sine(freq, pad_len, 1.0), 0.06, 1.4)])
    sig = mix(arp, at(int(SR * 0.70), pad, n))
    sig = remove_dc(sig)
    # slight stereo spread for the sting (allowed by the spec).
    # NOTE: the spread can exceed the mono peak, so fade + normalise BOTH
    # channels together afterwards - otherwise one channel clips the -6 dBFS
    # ceiling and the file does not end on zero.
    left = sig
    right = [0.0] * len(sig)
    delay = int(SR * 0.012)
    for i in range(delay, len(sig)):
        right[i] = sig[i] - 0.25 * sig[i - delay]
    left = fade_out(left)
    right = fade_out(right)
    peak = max(max(abs(v) for v in left), max(abs(v) for v in right))
    if peak:
        g = PEAK / peak
        left = [v * g for v in left]
        right = [v * g for v in right]
    return left, right


# ---------------------------------------------------------------- pipeline

def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(repo, "assets", "audio", "sfx")
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, "_wav")
    os.makedirs(tmp, exist_ok=True)

    jobs = [
        ("sfx_deploy", sfx_deploy, 1),
        ("sfx_hit", sfx_hit, 1),
        ("sfx_death", sfx_death, 1),
        ("sfx_mineral", sfx_mineral, 1),
        ("sfx_win", sfx_win, 2),
    ]
    want_ogg = "--ogg" in sys.argv
    for name, fn, channels in jobs:
        res = fn()
        if channels == 2:
            left, right = res
            wav = os.path.join(tmp, name + ".wav")
            inter = []
            for l, r in zip(left, right):
                inter += [l, r]
            write_wav(wav, inter, channels=2)
        else:
            wav = os.path.join(tmp, name + ".wav")
            write_wav(wav, res, channels=1)
        if want_ogg:
            ogg = os.path.join(out_dir, name + ".ogg")
            to_ogg(wav, ogg, channels)
            print("wrote", ogg)
        else:
            out = os.path.join(out_dir, name + ".wav")
            os.replace(wav, out)
            print("wrote", out)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


if __name__ == "__main__":
    main()
