#!/usr/bin/env python3
"""Ubah lyrics.txt (satu baris lirik per baris, boleh diawali [mm:ss]) menjadi lyrics.js
Pemakaian:  python3 convert_lyrics.py [lyrics.txt] [lyrics.js]
"""
import re, sys, json


def snake(words):
    s = "_".join(re.sub(r"[^\w]", "", w).lower() for w in words)
    return re.sub(r"_+", "_", s).strip("_") or "x"

def to_code(text, i):
    words = [w for w in re.split(r"\s+", text.strip()) if re.sub(r"[^\w]", "", w)]
    if not words or re.fullmatch(r"[.\-–—…\s]+", text.strip()):
        return "// ........"
    if len(words) == 1:
        return f'// {text.strip()}'
    if len(words) == 2:
        return f'{{ {snake(words[:1])}: "{snake(words[1:])}" }};'
    subj, verb = re.sub(r"[^\w]", "", words[0]).lower(), re.sub(r"[^\w]", "", words[1]).lower()
    rest = words[2:]
    if len(rest) == 1:
        return f'{subj}.{verb}( "{snake(rest)}" );'
    if len(rest) == 2:
        return f'{subj}.{verb}( "{snake(rest[:1])}" ){{ to: "{snake(rest[1:])}" }};'
    pat = i % 3
    if len(rest) < 3 or pat == 0:
        mid = max(1, len(rest) // 2)
        return f'{subj}.{verb}( "{snake(rest[:mid])}" ){{ {snake(rest[mid:2*mid][:1] or ["is"])}: "{snake(rest[mid:] or rest)}" }};'
    if pat == 1:
        return f'{subj}.{verb}( "{snake(rest[:1])}" ){{ {snake(rest[1:2])}: "{snake(rest[2:])}" }};'
    return f'{subj}.{verb}( "{snake(rest[:2])}" ){{ is: "{snake(rest[2:])}" }};'

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "lyrics.txt"
    dst = sys.argv[2] if len(sys.argv) > 2 else "lyrics.js"
    out = []
    for i, raw in enumerate(open(src, encoding="utf-8")):
        raw = raw.rstrip("\n")
        if not raw.strip():
            continue
        m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)", raw)
        t = None
        if m:
            t = int(m.group(1)) * 60 + float(m.group(2)); raw = m.group(3)
        out.append({"t": t, "code": to_code(raw, i)})

    with open(dst, "w", encoding="utf-8") as f:
        f.write("window.LYRICS = [\n")
        for o in out:
            t = "" if o["t"] is None else f't: {o["t"]}, '
            f.write(f'  {{ {t}code: {json.dumps(o["code"], ensure_ascii=False)} }},\n')
        f.write("];\n")
    print(f"{len(out)} baris ditulis ke {dst}")


def write_js(items, dst):
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('window.LYRICS = [\n')
        for o in items:
            t = '' if o['t'] is None else f't: {round(o["t"],2)}, '
            f.write(f'  {{ {t}code: {json.dumps(o["code"], ensure_ascii=False)} }},\n')
        f.write('];\n')


if __name__ == '__main__':
    main()
