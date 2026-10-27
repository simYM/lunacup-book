import pymupdf as fitz, json, re, sys
REV = sys.argv[1]
d = fitz.open('/mnt/user-data/uploads/20210907_인쇄용 최종/105-148더나은세상-TMI북 3쇄_20210907-176p.pdf')
b = json.load(open('book.json', encoding='utf-8'))
F = json.load(open('figs2.json'))
N = lambda s: re.sub(r'[^0-9A-Za-z가-힣]', '', s)
assert not any(any('보틀' in l for l in f['labels']) for f in F)

# drop loose label text that now lives inside the pictures, and any mini-bottle mention
labelsets = [N(''.join(f['labels'])) for f in F if f['labels']]
alllab = set(N(l) for f in F for l in f['labels'] if len(N(l)) >= 2)
for c in b:
    for s in c['sections']:
        nb = []
        for x in s['blocks']:
            t = N(x['x']) if isinstance(x['x'], str) else ''
            if '미니보틀' in t: continue
            if t and len(t) <= 40 and x['t'] in ('p', 'h') and (t in alllab or any(t in L for L in labelsets)): continue
            nb.append(x)
        s['blocks'] = nb

flat = []
for ci, c in enumerate(b):
    for si, s in enumerate(c['sections']):
        flat.append((ci, si, -1, N(s['title'])))
        for bi, x in enumerate(s['blocks']):
            if isinstance(x['x'], str): flat.append((ci, si, bi, N(x['x'])))

def plines(pg, lab):
    out = []
    for blk in d[pg-1].get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            t = ''.join(s['text'] for s in ln['spans']).strip()
            if len(N(t)) >= 6 and t not in lab: out.append((ln['bbox'][1], ln['bbox'][3], t))
    return sorted(out)

def find(t, start, win=90):
    k = N(t)
    for key in (k[-12:], k[:12], k[-8:]):
        if len(key) < 6: continue
        for j in range(start, min(len(flat), start + win)):
            if key in flat[j][3]: return j
    return None

BASE = f'https://cdn.jsdelivr.net/gh/simYM/lunacup-book@{REV}/fig2/'
place, cursor = {}, 0
for f in sorted(F, key=lambda f: (f['page'], f['bbox'][1])):
    L = plines(f['page'], set(f['labels'])); top, bot = f['bbox'][1], f['bbox'][3]
    j = None
    for cand in reversed([l for l in L if l[1] <= top + 3][-3:]):
        j = find(cand[2], cursor)
        if j is not None: break
    if j is None:
        for cand in [l for l in L if l[0] >= bot - 3][:3]:
            j = find(cand[2], cursor)
            if j is not None: j = max(j - 1, cursor); break
    if j is None: j = cursor
    cursor = j
    place.setdefault(j, []).append({'t': 'img', 'x': BASE + f['name'], 'alt': ' '.join(f['labels'])[:200], 'pg': f['page']})
for j in sorted(place, reverse=True):
    ci, si, bi, _ = flat[j]
    for k, im in enumerate(place[j]):
        b[ci]['sections'][si]['blocks'].insert(bi + 1 + k, im)

# brand pages belong at the start of the brand story
moved = []
for c in b:
    for s in c['sections']:
        keep = []
        for x in s['blocks']:
            if x['t'] == 'img' and x.get('pg') in (152, 153) and not s['title'].startswith('LUNACUP'): moved.append(x)
            else: keep.append(x)
        s['blocks'] = keep
for c in b:
    for s in c['sections']:
        if s['title'].startswith('LUNACUP STORY'): s['blocks'] = moved + s['blocks']
json.dump(b, open('book_full.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('placed', sum(len(v) for v in place.values()))
