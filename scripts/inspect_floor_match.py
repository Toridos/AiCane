import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
import run_navigation as rn

images = [
    (r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-1.png", 101, 118),
    (r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-2.png", 201, 223),
    (r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-3.png", 301, 332),
]

outdir = Path('outputs/ocr_match')
outdir.mkdir(parents=True, exist_ok=True)

for imgpath, start, end in images:
    print('\n== Inspecting', imgpath, f'expected {start}-{end} ==')
    texts = rn.run_ocr(imgpath)
    print('Detected tokens:', len(texts))
    # print tokens
    for k,v in list(texts.items())[:50]:
        print('  ', k, '->', v)

    mapping, missing = rn.match_ocr_to_expected(texts, start, end, max_dist=2)
    print('\nMapped tokens:')
    for exp in range(start, end+1):
        if exp in mapping:
            tok, pos, dist = mapping[exp]
            print(f'  {exp} => {tok} @ {pos} (dist={dist})')
        else:
            print(f'  {exp} => MISSING')

    print('\nMissing:', missing)
    # write a brief report
    rep = outdir / f'report_{Path(imgpath).stem}.txt'
    with open(rep, 'w', encoding='utf-8') as f:
        f.write(f'Image: {imgpath}\nExpected: {start}-{end}\n')
        f.write('Detected tokens:\n')
        for k,v in texts.items():
            f.write(f'  {k} -> {v}\n')
        f.write('\nMapping:\n')
        for exp in range(start, end+1):
            if exp in mapping:
                tok,pos,dist = mapping[exp]
                f.write(f'  {exp} => {tok} @ {pos} (dist={dist})\n')
            else:
                f.write(f'  {exp} => MISSING\n')
        f.write('\nMissing list:\n')
        for m in missing:
            f.write(str(m) + '\n')
    print('Wrote report to', rep)
