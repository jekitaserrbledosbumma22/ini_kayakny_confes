#!/usr/bin/env python3
"""Buat lyrics.js otomatis dari file lagu, lengkap dengan timing.

Instalasi (sekali saja, di komputermu):
    pip install faster-whisper
    (butuh ffmpeg terpasang)

Pemakaian:
    # Mode 1 – hanya lagu: lirik dikenali otomatis (akurasi tergantung lagu)
    python3 auto_sync.py assets/lagu.mp3

    # Mode 2 – lagu + teks lirik milikmu (lebih akurat, disarankan)
    python3 auto_sync.py assets/lagu.mp3 --lyrics lyrics.txt

Opsi: --model small|medium|large-v3  --lang id|en|auto
"""
import argparse, re, sys
from convert_lyrics import to_code, write_js


def transcribe(path, model_name, lang):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, compute_type="int8")
    segs, _ = model.transcribe(path, language=None if lang == "auto" else lang,
                               word_timestamps=True, vad_filter=True)
    words, lines = [], []
    for s in segs:
        lines.append((s.start, s.text.strip()))
        for w in (s.words or []):
            words.append((w.start, w.word.strip()))
    return words, lines


def align(lyric_lines, words):
    """Bagi baris lirik ke garis waktu kata yang dikenali, sebanding jumlah kata."""
    counts = [max(1, len(l.split())) for l in lyric_lines]
    total = sum(counts)
    out, acc = [], 0
    for line, c in zip(lyric_lines, counts):
        idx = min(len(words) - 1, int(acc / total * len(words)))
        out.append((words[idx][0], line))
        acc += c
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--lyrics")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="auto")
    ap.add_argument("--out", default="lyrics.js")
    a = ap.parse_args()

    words, lines = transcribe(a.audio, a.model, a.lang)
    if not words:
        sys.exit("Tidak ada suara terdeteksi.")
    if a.lyrics:
        raw = [re.sub(r"^\[[^\]]*\]\s*", "", l).strip() for l in open(a.lyrics, encoding="utf-8")]
        timed = align([l for l in raw if l], words)
    else:
        timed = lines
    items = [{"t": t, "code": to_code(text, i)} for i, (t, text) in enumerate(timed) if text]
    write_js(items, a.out)
    print(f"{len(items)} baris + timing ditulis ke {a.out}. Cek hasilnya lalu buka index.html")


if __name__ == "__main__":
    main()
