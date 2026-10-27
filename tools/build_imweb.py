import json, re, html
from annotate import annotate, render_text

b = json.load(open('book_full.json', encoding='utf-8'))
E = html.escape

# ---- cleanups ----
b[0]['sections'] = [s for s in b[0]['sections'] if len(s['blocks']) > 2]  # drop stub "입문자를 위한"
FIX = {
    '리오나 차머스가 미국 특허청에 접수한 실제 문서리 오 나 차 머 스 가 디 자 인 한 월 경 컵 은': '리오나 차머스가 디자인한 월경컵은',
    '실링(밀착)만 잘 되었다면괜찮습니다': '실링(밀착)만 잘 되었다면 괜찮습니다',
    '영양은 적지만': '영향은 적지만',
}
DROP = {'실링 해제를', '월경컵의 실링을', '월경컵 실링 해제법을', '영상으로 알아보기'}
for c in b:
    for s in c['sections']:
        nb, seen_h = [], set()
        for x in s['blocks']:
            if isinstance(x['x'], str):
                for k, v in FIX.items():
                    x['x'] = x['x'].replace(k, v)
                if x['x'].strip() in DROP:
                    continue
                if x['t'] == 'h':
                    if x['x'] in seen_h:
                        continue
                    seen_h.add(x['x'])
            nb.append(x)
        s['blocks'] = nb
        t = s['title']
        if t == '꼬리가 안 잡혀요.':
            txt = [x for x in s['blocks'] if x['t'] == 'p']
            for i, x in enumerate(s['blocks']):
                if x['t'] == 'p' and x['x'].startswith('편안한 마음으로 배변하듯'):
                    x['x'] = '편안한 마음으로 배변하듯 컵을 밀어냅니다. 너무 세게 힘을 줄 필요 없습니다. 천천히 5초 정도 힘을 주어 밀었다가 쉬고, 밀었다가 쉬고를 반복하면 꼬리가 잡힐 정도로 내려옵니다. 꼬리가 잡히면 천천히 잡아당긴 후 월경컵의 밑 부분을 눌러 실링을 해제하고 꺼내면 됩니다.'
                if x['t'] == 'p' and x['x'].startswith('었다가 쉬고'):
                    x['drop'] = True
            s['blocks'] = [x for x in s['blocks'] if not x.get('drop')]
        if t == '뺄 때 아파요.':
            for x in s['blocks']:
                if x['t'] == 'lead' and '월경컵이 질 벽과' in x['x']:
                    a, _, rest = x['x'].partition('월경컵이 질 벽과')
                    x['x'] = a.strip().rstrip('.') + '.'
                    x['_after'] = '월경컵이 질 벽과' + rest
            nb = []
            for x in s['blocks']:
                nb.append(x)
                if x.get('_after'):
                    nb.append({'t': 'p', 'x': x.pop('_after')})
            s['blocks'] = nb
        if t == '건조해서 보관':
            imgs = [x for x in s['blocks'] if x['t'] in ('img', 'imgs')]
            s['blocks'] = [{'t': 'p', 'x': '월경이 끝나면 열탕 소독한 뒤 완전히 말려서 보관해 주세요. 월경주기 동안의 관리는 이렇게 이어집니다.'},
                           {'t': 'steps', 'x': ['월경 시작: 열탕 소독 후 사용', '월경 중: 깨끗한 물에 씻어서 재사용', '월경 끝: 열탕 소독', '보관: 완전히 건조한 후 천 파우치나 통에 보관']}] + imgs

# 줄바꿈 때문에 소제목으로 잘못 떨어져 나온 문장 끝("있습니다." 등)을 앞 문단에 다시 붙이기
for c in b:
    for s in c['sections']:
        nb = []
        for x in s['blocks']:
            if x['t'] == 'h' and isinstance(x['x'], str) and len(x['x'].strip()) <= 10 and x['x'].strip().endswith('.') \
                    and nb and nb[-1]['t'] == 'p' and not nb[-1]['x'].rstrip().endswith(('.', '!', '?', '”', '"')):
                nb[-1]['x'] = nb[-1]['x'].rstrip() + ' ' + x['x'].strip(); continue
            nb.append(x)
        s['blocks'] = nb

# ---- 문단·소제목·그림 설명 정리 ----
from annotate import N as NN
ST = json.load(open('styles.json'))
BOXN = [NN(''.join(bx['lines'])) for bx in ST['boxes']]
SENT_END = ('.', '!', '?', '”', '"', '’', ')', ':', '…')
fixlog = {'merged': 0, 'caption': 0, 'heading': 0}

# 1) PDF 줄바꿈으로 끊긴 문단 잇기 ("분비되" / "지 않기 때문에")
for c in b:
    for s in c['sections']:
        nb = []
        for x in s['blocks']:
            if x['t'] == 'p' and nb and nb[-1]['t'] == 'p' and isinstance(x['x'], str):
                prev = nb[-1]['x'].rstrip()
                if len(prev) > 40 and re.search(r'[가-힣]$', prev) and not re.match(r'^\s*([>\-•①-⑩]|\d+[.)])', x['x']):
                    nb[-1]['x'] = prev + x['x'].lstrip(); fixlog['merged'] += 1; continue
            nb.append(x)
        s['blocks'] = nb

# 2) 그림 설명: 본문처럼 보이던 설명을 그림 아래 작은 글씨로
caps = sorted({NN(cp['text']) for cp in ST['captions'] if len(NN(cp['text'])) >= 6}, key=len, reverse=True)
FIGS = json.load(open('figs2.json'))
def cap_in_figure(nt):   # 그 설명이 이미 그림 이미지 안에 찍혀 있는지
    for cp in ST['captions']:
        if NN(cp['text']) != nt: continue
        r = cp['bbox']; cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        if any(f['page'] == cp['page'] and f['bbox'][0] <= cx <= f['bbox'][2] and f['bbox'][1] <= cy <= f['bbox'][3] for f in FIGS):
            return True
    return False
def in_box(nx): return any(nx in bn for bn in BOXN)
for c in b:
    for s in c['sections']:
        nb = []
        for x in s['blocks']:
            if x['t'] in ('p', 'h') and isinstance(x['x'], str) and not in_box(NN(x['x'])):
                nx = NN(x['x'])
                def glued(cp):  # 설명 뒤에 본문이 띄어쓰기 없이 바로 붙은 경우만 분리
                    if len(cp) < 12 or not (nx.startswith(cp) and len(nx) > len(cp) + 1): return False
                    k = 0
                    for i, ch in enumerate(x['x']):
                        if re.match(r'[0-9A-Za-z가-힣]', ch): k += 1
                        if k == len(cp): return i + 1 < len(x['x']) and not x['x'][i + 1].isspace()
                    return False
                hit = next((cp for cp in caps if nx == cp or glued(cp)), None)
                if hit:
                    if nx == hit:
                        cap_txt, rest = x['x'].strip(), ''
                    else:
                        k, cut = 0, 0
                        for i, ch in enumerate(x['x']):
                            if re.match(r'[0-9A-Za-z가-힣]', ch): k += 1
                            if k == len(hit): cut = i + 1; break
                        cap_txt, rest = x['x'][:cut].strip(), x['x'][cut:].strip()
                    cap = {'t': 'cap', 'x': cap_txt}
                    j = len(nb) - 1   # 바로 앞 그림 밑으로
                    while j >= 0 and j >= len(nb) - 4 and nb[j]['t'] != 'img': j -= 1
                    if cap_in_figure(hit) or (j >= 0 and nb[j]['t'] == 'img' and NN(cap_txt) in NN(nb[j].get('alt', ''))):
                        pass   # 그림 안에 이미 찍혀 있는 설명이면 빼기
                    elif j >= 0 and nb[j]['t'] == 'img':
                        k2 = j + 1
                        while k2 < len(nb) and nb[k2]['t'] == 'cap': k2 += 1
                        nb.insert(k2, cap)
                    else:
                        nb.append(cap)
                    fixlog['caption'] += 1
                    if rest: nb.append(dict(x, x=rest))
                    continue
            nb.append(x)
        s['blocks'] = nb

# 3) 그림 이름표와 이름이 같아 지워졌던 소제목 되살리기 (음핵, 요도, 항문, 포궁, 질 …)
have = {NN(x['x']) for c in b for s in c['sections'] for x in s['blocks'] if isinstance(x['x'], str)}
have |= {NN(s['title']) for c in b for s in c['sections']}
for r in ST['runs']:
    ht, af = r['text'].strip(), r.get('after')
    if not af or r['size'] < 8.8 or len(ht) > 30 or '“' in ht or NN(ht) in have: continue
    done = False
    for c in b:
        for s in c['sections']:
            for i, x in enumerate(s['blocks']):
                if x['t'] not in ('p', 'lead') or not isinstance(x['x'], str): continue
                nx = NN(x['x'])
                if af in nx:
                    if nx.startswith(af):
                        s['blocks'].insert(i, {'t': 'h', 'x': ht, 'cls': r['cat']})
                    else:
                        k, cut = 0, 0
                        target = nx.index(af)
                        for ci, ch in enumerate(x['x']):
                            if re.match(r'[0-9A-Za-z가-힣]', ch):
                                if k == target: cut = ci; break
                                k += 1
                        head, tail = x['x'][:cut].rstrip(), x['x'][cut:]
                        s['blocks'][i:i + 1] = [dict(x, x=head), {'t': 'h', 'x': ht, 'cls': r['cat']}, dict(x, x=tail, t='p')]
                    fixlog['heading'] += 1; have.add(NN(ht)); done = True; break
            if done: break
        if done: break
print('fix', fixlog)

STATS = annotate(b, json.load(open('styles.json')))
print('styles', STATS)

import manual
BASE_URL = next(x['x'] for c in b for s in c['sections'] for x in s['blocks'] if x['t']=='img').rsplit('/',1)[0]+'/'
manual.apply(b, ST)
json.dump(b, open('final.json','w',encoding='utf-8'), ensure_ascii=False)
# ---- ids ----
n = 0
for c in b:
    for s in c['sections']:
        n += 1
        s['sid'] = f's{n:02d}'

def block(x):
    t = x['t']
    if t == 'img':
        return f'<figure class="lcb-fig"><div class="lcb-pics"><img src="{x["x"]}" alt="{E(x.get("alt",""))}" loading="lazy"></div></figure>'
    if t == 'imgs':
        return '<figure class="lcb-fig"><div class="lcb-pics lcb-two">' + ''.join(f'<img src="{u}" alt="" loading="lazy">' for u in x['x']) + '</div></figure>'
    if t == 'cap':
        return f'<p class="lcb-cap">{E(x["x"])}</p>'
    if t == 'panel':
        inner = ''
        for k, v in x['parts']:
            if k == 'h': inner += f'<p class="lcb-pn-h">{E(v)}</p>'
            elif k == 'sub': inner += f'<p class="lcb-pn-s">{E(v)}</p>'
            elif k == 'ul': inner += '<ul>' + ''.join(f'<li>{E(i)}</li>' for i in v) + '</ul>'
            else: inner += '<p>' + E(v).replace('&lt;br&gt;', '<br>') + '</p>'
        return f'<div class="lcb-panel lcb-panel-{x["theme"]}" style="background-image:url({x["img"]})"><div class="lcb-pn-in">{inner}</div></div>'
    if t == 'btns':
        return '<div class="lcb-btns">' + ''.join(f'<a class="lcb-btn" href="{E(u)}" target="_blank" rel="noopener">{E(l)}</a>' for l, u in x['x']) + '</div>'
    if t == 'grid':
        return '<div class="lcb-grid">' + ''.join(
            '<figure>' + (f'<h4>{E(i["title"])}</h4>' if i.get('title') else '') + f'<img src="{i["img"]}" alt="" loading="lazy">'
            + ''.join(f'<p>{E(p)}</p>' for p in i['text']) + '</figure>' for i in x['x']) + '</div>'
    if t == 'isteps':
        return '<ol class="lcb-isteps">' + ''.join(
            f'<li><img src="{i["img"]}" alt="{E(i["title"])}" loading="lazy"><div><strong>{E(i["title"])}</strong><span>{E(i["text"])}</span></div></li>'
            for i in x['x']) + '</ol>'
    if t == 'steps':
        return '<ol class="lcb-steps">' + ''.join(f'<li><span>{E(i)}</span></li>' for i in x['x']) + '</ol>'
    cls = []
    if x.get('cls'): cls.append('lcb-p-' + x['cls'])
    if x.get('big'): cls.append('lcb-big')
    if x.get('boxhead'): cls.append('lcb-boxhead')
    inner = render_text(x['x'], x.get('marks'))
    if x.get('link'):
        lt, target = x['link']
        sid = target[1:] if target.startswith('#') else next(s['sid'] for c in b for s in c['sections'] if s['title'].startswith(target))
        inner = inner.replace(E(lt), f'<a class="lcb-link" href="#{sid}" data-go="{sid}">{E(lt)}</a>', 1)
    short_head = t == 'p' and x.get('cls') and not x.get('big') and len(x['x'].strip()) <= 30 \
        and not x['x'].strip().endswith(('.', '다', '요')) and not x.get('box')
    if t in ('lead', 'h') or short_head: cls.insert(0, 'lcb-lead')
    aid = f' id="{x["anchor"]}"' if x.get('anchor') else ''
    return f'<p{aid} class="{" ".join(cls)}">{inner}</p>' if cls else f'<p{aid}>{inner}</p>'

def render_blocks(blocks):
    out, i = [], 0
    while i < len(blocks):
        bx = blocks[i].get('box')
        if bx:
            j = i
            while j < len(blocks) and blocks[j].get('box') == bx: j += 1
            out.append(f'<div class="lcb-box lcb-box-{bx[1]}">' + ''.join(block(y) for y in blocks[i:j]) + '</div>')
            i = j
        else:
            out.append(block(blocks[i])); i += 1
    return ''.join(out)

QK = '<span class="lcb-qk">Q</span>'
toc, body = [], []
for c in b:
    items = ''.join(
        f'<li><a href="#{s["sid"]}" data-go="{s["sid"]}">{QK if s["kind"]=="qa" else ""}<span>{E(s["title"].rstrip("."))}</span></a></li>'
        for s in c['sections'])
    toc.append(f'<div class="lcb-ch">{E(c["title"])}</div><ul>{items}</ul>')
    secs = ''.join(
        f'<section class="lcb-sec{" lcb-q" if s["kind"]=="qa" else ""}" id="{s["sid"]}">'
        f'<h3 class="lcb-h"><button type="button" class="lcb-tg" aria-expanded="false" aria-controls="{s["sid"]}-b">'
        f'<span class="lcb-tt">{E(s["title"].rstrip("."))}</span><span class="lcb-chev" aria-hidden="true"></span></button></h3>'
        f'<div class="lcb-body" id="{s["sid"]}-b" hidden>{render_blocks(s["blocks"])}'
        f'<div class="lcb-foot"><button type="button" class="lcb-copy" data-copy="{s["sid"]}">이 항목 링크 복사</button></div></div></section>'
        for s in c['sections'])
    body.append(f'<h2 class="lcb-chapter">{E(c["title"])}</h2>{secs}')

tpl = open('imweb_template.html', encoding='utf-8').read()
COVER = f'<figure class="lcb-cover"><img src="{BASE_URL}cover.jpg" alt="월경컵 입문자를 위한 월경컵 TMI 표지"></figure>'
out = tpl.replace('__TOC__', ''.join(toc)).replace('__BODY__', COVER + ''.join(body))
open('/home/claude/lunacup-book/imweb-book.html', 'w', encoding='utf-8').write(out)
print('sections', n, 'bytes', len(out.encode()))
