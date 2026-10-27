"""PDF에서 강조 스타일(밑줄, 색 강조, 박스)을 뽑아 styles.json으로 저장"""
import pymupdf as fitz, json, re

PDF = '/mnt/user-data/uploads/20210907_인쇄용 최종/105-148더나은세상-TMI북 3쇄_20210907-176p.pdf'
d = fitz.open(PDF)
N = lambda s: re.sub(r'[^0-9A-Za-z가-힣]', '', s)

def hexc(c):
    return '#%02x%02x%02x' % tuple(int(v * 255) for v in c) if c else None

def near(c, target, tol=40):
    if not c: return False
    a = [int(c[i:i+2], 16) for i in (1, 3, 5)]; b = [int(target[i:i+2], 16) for i in (1, 3, 5)]
    return sum(abs(x - y) for x, y in zip(a, b)) <= tol

def span_cat(s):
    c = '#%06x' % s['color']; size = s['size']; font = s['font']
    if 'Jalnan' in font or size < 7.4: return None          # 제목/쪽번호/머리글
    if near(c, '#00aeef'): return 'blue'
    if near(c, '#40ad49'): return 'green'
    if near(c, '#693293') and size <= 11.5 and 'GongPen' not in font: return 'purple'
    if (near(c, '#ec008c') or near(c, '#ee3c96')) and size <= 13.5:
        return None if s['text'].strip().startswith('Q') else 'pink'
    return None

out = {'underline': [], 'runs': [], 'boxes': [], 'pages': {}, 'captions': []}
for pi in range(9, 172):
    p = d[pi]; pg = pi + 1
    raw = p.get_text('rawdict')
    lines = []
    for b in raw['blocks']:
        for ln in b.get('lines', []):
            chars = [ch for sp in ln['spans'] for ch in sp['chars']]
            for sp in ln['spans']: sp['text'] = ''.join(ch['c'] for ch in sp['chars'])
            if chars: lines.append({'bbox': fitz.Rect(ln['bbox']), 'chars': chars, 'spans': ln['spans']})
    imgs = [fitz.Rect(i['bbox']) for i in p.get_image_info()]
    out['pages'][pg] = N(p.get_text())

    # --- 밑줄: 분홍 가로선(두께 ~1) ---
    segs = []
    for dr in p.get_drawings():
        r = dr['rect']; st = hexc(dr.get('color'))
        if r.x0 < 60 or r.x1 > 311 or r.y0 < 30 or r.y1 > 412: continue
        if not st or not near(st, '#ec008b', 60): continue
        if r.height > 1.5 or r.width < 5 or abs((dr.get('width') or 0) - 1.0) > 0.3: continue
        if any(it[0] != 'l' for it in dr['items']): continue
        txt = ''.join(ch['c'] for l in lines for ch in l['chars']
                      if r.y0 - 6 <= ch['bbox'][3] <= r.y0 + 1.5 and r.x0 - 1 <= (ch['bbox'][0] + ch['bbox'][2]) / 2 <= r.x1 + 1)
        if N(txt): segs.append((r, txt))
    segs.sort(key=lambda s: (s[0].y0, s[0].x0))
    merged = []
    for r, t in segs:  # 줄바꿈으로 이어지는 밑줄을 한 덩어리로
        if merged:
            pr, pt = merged[-1]
            if 8 <= r.y0 - pr.y0 <= 18 and pr.x1 > 280 and r.x0 < 95:
                merged[-1] = (pr | r, pt + t); continue
        merged.append((r, t))
    for r, t in merged:
        out['underline'].append({'page': pg, 'text': t})

    # --- 색 강조: 같은 색이 이어지는 구간 ---
    cur = None
    for l in lines:
        for sp in l['spans']:
            cat = span_cat(sp)
            t = sp['text']
            if cat and cur and cur['cat'] == cat and abs(l['bbox'].y0 - cur['y']) < 22:
                cur['text'] += t; cur['y'] = l['bbox'].y0; cur['y1'] = l['bbox'].y1
            elif cat:
                if cur: out['runs'].append(cur)
                cur = {'page': pg, 'cat': cat, 'text': t, 'y': l['bbox'].y0, 'y1': l['bbox'].y1, 'x0': l['bbox'].x0, 'size': round(sp['size'], 1)}
            elif N(t) and cur:
                out['runs'].append(cur); cur = None
    if cur: out['runs'].append(cur)
    # 소제목 바로 다음 본문 줄 (빠진 소제목을 다시 넣을 위치)
    body_lines = [l for l in lines if any('SDAchim-aLt' in sp['font'] and sp['size'] > 7.5 for sp in l['spans'])]
    for r in out['runs']:
        if r['page'] != pg or r['size'] < 8.8 or 'after' in r: continue
        col = 0 if r['x0'] < 185 else 1
        nxt = [l for l in body_lines if l['bbox'].y0 >= r['y1'] - 1 and (0 if l['bbox'].x0 < 185 else 1) == col]
        nxt.sort(key=lambda l: l['bbox'].y0)
        if nxt: r['after'] = N(''.join(ch['c'] for ch in nxt[0]['chars']))[:14]
    # 그림 설명(작은 고딕체) 블록
    for b in raw['blocks']:
        spans = [sp for ln in b.get('lines', []) for sp in ln['spans'] if N(''.join(ch['c'] for ch in sp['chars']))]
        if spans and all('NanumSquare' in sp['font'] and sp['size'] <= 7.0 for sp in spans):
            t = ''.join(''.join(ch['c'] for ch in sp['chars']) for sp in spans)
            out['captions'].append({'page': pg, 'text': t, 'bbox': list(b['bbox'])})

    # --- 박스: 초록 테두리 / 회색 바탕 둥근 사각형 ---
    rects = []
    for dr in p.get_drawings():
        r = dr['rect']
        if r.width < 60 or r.height < 12 or r.x0 < 60 or r.x1 > 311: continue
        kinds = [it[0] for it in dr['items']]
        if 'c' not in kinds or 'l' not in kinds: continue
        fill, st = hexc(dr.get('fill')), hexc(dr.get('color'))
        style = None
        if st and near(st, '#40ad48', 60): style = 'green'
        elif fill and near(fill, '#dbdcde', 30): style = 'grey'
        if not style: continue
        if any((r & im).get_area() > 0.3 * r.get_area() for im in imgs): continue
        rects.append([r, style])
    rects.sort(key=lambda x: x[0].y0)
    boxes = []
    for r, st in rects:  # 이어 붙은 회색 띠는 하나로
        if boxes and boxes[-1][1] == st and r.y0 - boxes[-1][0].y1 < 4 and abs(r.x0 - boxes[-1][0].x0) < 3:
            boxes[-1][0] = boxes[-1][0] | r
        else: boxes.append([r, st])
    for k, (r, st) in enumerate(boxes):
        inner = [''.join(ch['c'] for ch in l['chars']) for l in lines if r.contains(fitz.Point((l['bbox'].x0 + l['bbox'].x1) / 2, (l['bbox'].y0 + l['bbox'].y1) / 2))]
        if inner: out['boxes'].append({'id': f'b{pg}-{k}', 'page': pg, 'style': st, 'lines': inner})

for r in out['runs']:
    for k in ('y', 'y1', 'x0'): r.pop(k, None)
json.dump(out, open('styles.json', 'w'), ensure_ascii=False, indent=0)
print({k: len(v) for k, v in out.items() if k != 'pages'})
import collections; print(collections.Counter(r['cat'] for r in out['runs']))
