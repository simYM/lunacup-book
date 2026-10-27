"""styles.json(PDF 강조 정보)를 웹북 문단에 연결: 문단 색, 문장 안 색/밑줄 구간, 박스 묶음"""
import json, re, html

KEEP = re.compile(r'[0-9A-Za-z가-힣]')
N = lambda s: ''.join(KEEP.findall(s))
E = html.escape
OPEN_P = '‘“(\'"['
CLOSE_P = '’”)!?.\'"]~'

def norm_map(s):
    pos = [i for i, ch in enumerate(s) if KEEP.match(ch)]
    return ''.join(s[i] for i in pos), pos

def to_range(s, pos, a, b, raw):
    st, en = pos[a], pos[b - 1] + 1
    raw = raw.strip()
    while st > 0 and s[st - 1] in OPEN_P and raw[:1] in OPEN_P: st -= 1
    while en < len(s) and s[en] in CLOSE_P and s[en] in raw: en += 1
    return st, en

def page_of(nx, pages, cursor):
    key = nx[:14] if len(nx) >= 14 else nx
    if len(key) < 4: return cursor
    order = list(range(cursor, 176)) + list(range(10, cursor))
    for pg in order:
        if key in pages.get(pg, ''): return pg
    return cursor

def annotate(book, styles):
    pages = {int(k): v for k, v in styles['pages'].items()}
    runs = [dict(r, n=N(r['text'])) for r in styles['runs'] if N(r['text'])]
    unds = [dict(u, n=N(u['text'])) for u in styles['underline'] if len(N(u['text'])) >= 3]
    boxes = [dict(bx, n=N(''.join(bx['lines']))) for bx in styles['boxes']]
    near = lambda item, pg: abs(item['page'] - pg) <= 1
    stats = {'para': 0, 'inline': 0, 'underline': 0, 'box': 0, 'split': 0}
    cursor = 10
    for c in book:
        for s in c['sections']:
            nb = []
            for x in s['blocks']:
                if x['t'] not in ('p', 'lead', 'h') or not isinstance(x['x'], str):
                    nb.append(x); continue
                text = x['x']; nx, pos = norm_map(text)
                if not nx: nb.append(x); continue
                pg = cursor = page_of(nx, pages, cursor)
                # 박스 마지막 줄이 다음 문단과 붙어버린 경우: 박스 부분만 떼어내기
                for bx in boxes:
                    if not near(bx, pg) or nx in bx['n']: continue
                    k = next((k for k in range(len(nx) - 1, 7, -1) if bx['n'].endswith(nx[:k])), 0)
                    if k:
                        cut = pos[k - 1] + 1
                        while cut < len(text) and text[cut] in CLOSE_P: cut += 1
                        nb.append({'t': 'p', 'x': text[:cut].strip(), 'box': [bx['id'], bx['style']]})
                        text = x['x'] = text[cut:].strip(); nx, pos = norm_map(text); stats['box'] += 1
                        break
                for bx in boxes:
                    if near(bx, pg) and len(nx) >= 4 and nx in bx['n']:
                        x['box'] = [bx['id'], bx['style']]; stats['box'] += 1; break
                pre, post, marks = None, None, []
                for r in runs:
                    if not near(r, pg): continue
                    rn = r['n']
                    if nx == rn or (len(nx) >= 4 and nx in rn) or (len(rn) >= 4 and rn in nx and len(rn) >= 0.6 * len(nx)):
                        x['cls'] = r['cat']
                        if r.get('size', 0) >= 9.95 and x['t'] == 'p': x['big'] = True
                        stats['para'] += 1; break
                else:
                    for r in runs:
                        rn = r['n']
                        if not near(r, pg) or len(rn) < 4 or rn not in nx: continue
                        a = nx.index(rn); st, en = to_range(text, pos, a, a + len(rn), r['text'])
                        heading = (r.get('size', 0) >= 8.8 or len(rn) <= 22) and not r['text'].strip().endswith(('.', '다'))
                        if heading and st == 0 and en < len(text):      # 문단 앞에 붙은 소제목은 따로 떼기
                            pre = {'t': 'h', 'x': text[:en].strip(), 'cls': r['cat']}; stats['split'] += 1
                        elif heading and en >= len(text.rstrip()) and st > 0:   # 문단 끝에 붙은 소제목
                            post = {'t': 'h', 'x': text[st:].strip(), 'cls': r['cat']}; stats['split'] += 1
                        elif len(rn) >= 8:
                            marks.append((st, en, 'c-' + r['cat'])); stats['inline'] += 1
                if pre: text = text[len(pre['x']):].lstrip()
                if post: text = text[:len(text) - len(post['x'])].rstrip()
                if pre or post:
                    x['x'] = text; nx, pos = norm_map(text); marks = []
                for u in unds:
                    un = u['n']
                    if near(u, pg) and un in nx:
                        a = nx.index(un); marks.append((*to_range(text, pos, a, a + len(un), u['text']), 'u')); stats['underline'] += 1
                if marks: x['marks'] = marks
                if pre: nb.append(pre)
                if x['x'].strip(): nb.append(x)
                if post: nb.append(post)
            s['blocks'] = nb
    return stats

def render_text(text, marks):
    if not marks: return E(text)
    cuts = sorted({0, len(text), *[m[0] for m in marks], *[m[1] for m in marks]})
    out = []
    for a, b in zip(cuts, cuts[1:]):
        cls = sorted({m[2] for m in marks if m[0] <= a and b <= m[1]})
        seg = E(text[a:b])
        out.append(f'<span class="{" ".join("lcb-" + k for k in cls)}">{seg}</span>' if cls else seg)
    return ''.join(out)
