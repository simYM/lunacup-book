import pymupdf as fitz, json, os, re, shutil
from PIL import Image

PDF = '/mnt/user-data/uploads/20210907_인쇄용 최종/105-148더나은세상-TMI북 3쇄_20210907-176p.pdf'
OUT = '/home/claude/lunacup-book/fig2/'
d = fitz.open(PDF)
book = json.load(open('book.json', encoding='utf-8'))
N = lambda s: re.sub(r'[^0-9A-Za-z가-힣]', '', s)
# long paragraphs of the book body: any PDF text block contained in these is body text, not a figure label
body_paras = [N(x['x']) for c in book for s in c['sections'] for x in s['blocks'] if isinstance(x['x'], str) and len(N(x['x'])) > 40]
def is_body(t):
    k = N(t)
    return len(k) >= 10 and any(k in p for p in body_paras)

SKIP = set(range(1, 10)) | {173, 174, 175, 176}
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
figs = []
from PIL import ImageChops
def trim(im, pad=18):
    g = ImageChops.difference(im, Image.new('RGB', im.size, 'white')).convert('L').point(lambda v: 255 if v > 14 else 0)
    bb = g.getbbox()
    if not bb: return im
    bb = (max(0, bb[0]-pad), max(0, bb[1]-pad), min(im.width, bb[2]+pad), min(im.height, bb[3]+pad))
    return im.crop(bb)
OVR = {150: [(110, 95, 262, 386)], 141: [(95, 300, 300, 405)], 104: [(191, 199, 312, 319)], 49: [(80, 186, 296, 413)], 54: [(90, 110, 282, 372)], 58: [(70, 71, 141, 170)], 51: [(85, 146, 274, 359)], 60: [(74, 75, 297, 312)], 152: [(31, 32, 344, 461)]}
SKIPFIG = {(66, 0), (81, 0)}          # 66: 67쪽 원본 그림 하나로 대체 / 81: 무료 월경교육 QR(삭제 요청)
ERASE_TXT = {89: ('넣기',), 63: ('탄성 체크법', '30초간', '손을 폈을', '찌그러진'), 94: ('착용 방향과 위치',), 87: ('접기는 쉽지만',)}
ORIG = {'f030-0.jpg': '/mnt/user-data/uploads/20210907_인쇄용 최종/img/02/02_p30.png', 'f067-0.jpg': '/mnt/user-data/uploads/20210907_인쇄용 최종/img/03/03_P67.jpg'}
cropped_log = []
erase_map = {}
clean = fitz.open(PDF)
for pi in range(d.page_count):
    pg = pi + 1
    if pg in SKIP: continue
    p = d[pi]; pr = p.rect
    cores = [fitz.Rect(i['bbox']) & pr for i in p.get_image_info() if (i['bbox'][2]-i['bbox'][0]) > 25 and (i['bbox'][3]-i['bbox'][1]) > 25]
    cores = [c for c in cores if not c.is_empty]
    merged = True
    while merged:
        merged = False
        for i in range(len(cores)):
            for j in range(i+1, len(cores)):
                a = fitz.Rect(cores[i]) + (-14, -14, 14, 14)
                if a.intersects(cores[j]):
                    cores[i] = cores[i] | cores[j]; cores.pop(j); merged = True; break
            if merged: break
    # text blocks classified as body text or label
    blocks = []
    for blk in p.get_text('dict')['blocks']:
        lines = [(fitz.Rect(ln['bbox']), ''.join(s['text'] for s in ln['spans']).strip()) for ln in blk.get('lines', [])]
        lines = [l for l in lines if l[1]]
        if not lines: continue
        txt = ''.join(t for _, t in lines)
        body = is_body(txt) or any(is_body(t) and len(N(t)) >= 14 for _, t in lines)
        fonts = [sp['font'] for ln in blk.get('lines', []) for sp in ln['spans'] if sp['text'].strip()]
        if fonts and all('NanumSquare' in f for f in fonts) and max(sp['size'] for ln in blk['lines'] for sp in ln['spans']) <= 7.2:
            body = False
        blocks.append((fitz.Rect(blk['bbox']), lines, body))
    if pg in OVR:
        cores = [fitz.Rect(r) for r in OVR[pg]]
    for k, core in enumerate(cores):
        if (pg, k) in SKIPFIG: continue
        bx = fitz.Rect(core); labels = []
        for r, lines, body in blocks:
            if body: continue
            for lr, t in lines:
                if (fitz.Rect(bx) + (-8, -8, 8, 8)).intersects(lr) and not t.isdigit():
                    bx |= lr; labels.append(t)
        # trim away body text that overlaps the figure box
        for r, lines, body in blocks:
            if not body or not r.intersects(bx): continue
            cx = (core.x0 + core.x1) / 2; cy = (core.y0 + core.y1) / 2
            rx = (r.x0 + r.x1) / 2
            if r.width < core.width * 0.8:            # a text column beside the picture
                if rx > cx: bx.x1 = min(bx.x1, r.x0 - 2)
                else: bx.x0 = max(bx.x0, r.x1 + 2)
            else:                                     # a paragraph above or below
                if (r.y0 + r.y1) / 2 < cy: bx.y0 = max(bx.y0, r.y1 + 2)
                else: bx.y1 = min(bx.y1, r.y0 - 2)
        untrimmed = fitz.Rect(core)
        if pg in OVR: bx = fitz.Rect(core)
        for r, lines, body in blocks:
            if body: continue
            for lr, t in lines:
                if pg not in OVR and (fitz.Rect(untrimmed) + (-8, -8, 8, 8)).intersects(lr): untrimmed |= lr
        if pg < 150:
            # 그림 영역은 자르지 않고 통째로 두고, 그 위에 겹친 본문·쪽번호·머리글 글자만 지움
            bx = fitz.Rect(untrimmed)
            erase = []
            for blk2 in p.get_text('dict')['blocks']:
                for ln in blk2.get('lines', []):
                    ltxt = ''.join(sp['text'] for sp in ln['spans']).strip()
                    lbody = is_body(ltxt) or any(fitz.Rect(blk2['bbox']) == r and body for r, _, body in blocks)
                    for sp in ln['spans']:
                        sr = fitz.Rect(sp['bbox']); t = sp['text'].strip()
                        if not t or not sr.intersects(bx): continue
                        f = sp['font']; c = sp['color']
                        if 'Jalnan' in f and sp['size'] < 8: erase.append(sr); continue          # 쪽번호
                        if 'SDAchim' in f and sp['size'] < 6.2: erase.append(sr); continue       # 머리글
                        if 'SDAchim' in f and c != 0xffffff and pg not in (46, 49): erase.append(sr); continue  # 본문·강조문
                        if any(k in ltxt for k in ERASE_TXT.get(pg, ())): erase.append(sr)
            for dr in p.get_drawings():   # 쪽번호 옆 파란 짧은 선 같은 장식
                r = dr['rect'] + (-1, -1, 1, 1); col = dr.get('color') or dr.get('fill')
                if not col or not r.intersects(bx) or r.height >= 5: continue
                cyan = abs(col[0]) < 0.1 and col[2] > 0.8 and r.width < 25
                pink = col[0] > 0.85 and col[1] < 0.15 and col[2] > 0.4 and r.y0 > 60     # 지운 본문의 분홍 밑줄
                if cyan or pink: erase.append(('line', r + (-2, -2, 2, 2)))
            if erase:
                erase_map[(pg, k)] = erase; cropped_log.append(f'{pg}-{k}')
        elif bx.is_empty or bx.width * bx.height < 0.35 * core.width * core.height:
            bx = fitz.Rect(untrimmed)
        bx = (bx + (-4, -4, 4, 4)) & pr
        if bx.width < 30 or bx.height < 30: continue
        if any('보틀' in l for l in labels): continue       # mini bottle discontinued
        name = f'f{pg:03d}-{k}.jpg'
        if (pg, k) in erase_map:
            cp = clean[pi]
            for r in erase_map[(pg, k)]:
                if not isinstance(r, tuple): cp.add_redact_annot(r + (-1, -1, 1, 1), fill=None)
            cp.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
            lines_ = [r for r in erase_map[(pg, k)] if isinstance(r, tuple)]
            pix = cp.get_pixmap(dpi=300, clip=bx, alpha=False)
        else:
            pix = p.get_pixmap(dpi=300, clip=bx, alpha=False)
        im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        from PIL import ImageDraw
        sc = pix.width / bx.width
        for r in erase_map.get((pg, k), []):
            if isinstance(r, tuple):
                r = r[1]
                ImageDraw.Draw(im).rectangle([(r.x0 - bx.x0) * sc, (r.y0 - bx.y0) * sc, (r.x1 - bx.x0) * sc, (r.y1 - bx.y0) * sc], fill='white')
        if name in ORIG:
            o = Image.open(ORIG[name])
            if o.mode in ('RGBA', 'LA', 'P'):
                o = o.convert('RGBA'); im = Image.new('RGB', o.size, 'white'); im.paste(o, mask=o.split()[-1])
            else: im = o.convert('RGB')
        im = trim(im)
        if im.width > 1360: im = im.resize((1360, round(im.height * 1360 / im.width)), Image.LANCZOS)
        im.save(OUT + name, 'JPEG', quality=80, optimize=True, progressive=True)
        figs.append({'page': pg, 'name': name, 'bbox': [bx.x0, bx.y0, bx.x1, bx.y1], 'labels': labels})
json.dump(figs, open('figs2.json', 'w'), ensure_ascii=False)
print('cropped', cropped_log); print(len(figs), sum(os.path.getsize(OUT + f['name']) for f in figs) // 1024, 'KB')
