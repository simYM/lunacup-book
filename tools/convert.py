import re, json

pages = {int(k): v for k, v in json.load(open('pages.json', encoding='utf-8')).items()}

CHAPTERS = [
    ('intro', '들어가는 글', 10, 12),
    ('c1', '1. 알아두면 좋은 정보', 13, 18),
    ('c2', '2. 내 몸과 만나는 시간', 19, 54),
    ('c3', '3. 반갑다, 월경컵!', 55, 82),
    ('c4', '4. 월경컵 사용법', 83, 116),
    ('c5', '5. 월경컵 관리법', 117, 130),
    ('c6', '6. 많이 하는 질문', 131, 150),
    ('c7', '7. 루나컵 소개', 151, 162),
    ('c8', '8. 월경교육으로 새로 고침', 163, 172),
]
TITLE_PAGES = {13, 19, 55, 83, 117, 131, 151, 163}
RUNNING = {'1. 알아두면 좋은 정보!', '2. 내 몸과 만나는 시간', '3. 반갑다. 월경컵!', '4. 월경컵 사용법',
           '5. 월경컵 관리법', '6. 많이 하는 질문', '7. 루나컵 소개', '8. 월경교육으로 새로 고침',
           '루나컵 소개', '8.', '7.', '6.', '5.', '4.'}

def ns(s):
    return re.sub(r'\s+', '', s)

# section headings (h2): exact line text per page -> display title
H2 = {
    11: {'들어가는 글': '들어가는 글'},
    14: {'생리 vs 월경': '생리 vs 월경'},
    15: {'자궁 vs 포궁': '자궁 vs 포궁'},
    16: {'처녀막 vs 질 막(질 주름)': '처녀막 vs 질 막(질 주름)'},
    21: {'1. 거울로 만나는 외음부': '거울로 만나는 외음부'},
    30: {'2. 신비로운 내성기': '신비로운 내성기'},
    41: {'3. 내 몸의 리듬, 월경': '내 몸의 리듬, 월경'},
    56: {'1. 월경컵 연대기': '월경컵 연대기'},
    59: {'2. 월경컵 소재와 구조': '월경컵 소재와 구조'},
    62: {'3. 월경컵의 경도와 탄성': '월경컵의 경도와 탄성'},
    64: {'4. 월경컵에 도전하는 우리의 자세': '월경컵에 도전하는 우리의 자세'},
    69: {'5. 나에게 맞는 월경컵은?': '나에게 맞는 월경컵은?'},
    73: {'나의 질 길이는?': '나의 질 길이는?'},
    84: {'1 접기': '접기'},
    88: {'2 착용하기': '착용하기'},
    108: {'3 비우고 교체하기': '비우고 교체하기'},
    118: {'사용 전, 사용 후 열탕 소독': '사용 전, 사용 후 열탕 소독'},
    120: {'세척하여 재사용': '세척하여 재사용'},
    121: {'건조해서 보관': '건조해서 보관'},
    152: {'LUNACUP STORY: BRAND': 'LUNACUP STORY: BRAND'},
    156: {'왜, 루나컵을 선택하나요?': '왜, 루나컵을 선택하나요?'},
    164: {'월경 그리고 혐오': '월경 그리고 혐오'},
    166: {'한부모가정의 고민': '한부모가정의 고민', '초경, 왜 축하해요?': '초경, 왜 축하해요?'},
    168: {'월경, 그 무한한 가능성': '월경, 그 무한한 가능성'},
    170: {'가문의 원수라도 생리대는 빌려준다!': '가문의 원수라도 생리대는 빌려준다!'},
    171: {'월경에 진심, 월경 교육으로 새로 고침!': '월경에 진심, 월경 교육으로 새로 고침!'},
}
H3 = {  # sub headings
    '라비아 접기', '하프다이아 접기', '펀치다운 접기', 'C자 접기', '준비자세', '넣기',
    '펴주고 실링(진공) 확인하기', '실링(진공) 확인 요령', '월경컵 교체하는 방법', '끓인 물에 열탕 소독하기',
    '열탕소독이란?', '넘쳐서 샌 경우', '실링이 안 된 경우', '살짝 묻어나는 경우', '왜 월경량은 개인마다 다를까?',
    '음모', '대음순과 소음순', '요도', '질 입구와 질 막(질 주름)', '항문', '난소와 난자', '나팔관(난관)',
    '월경 기간과 월경량', '월경혈은 더러울까?', '월경통', '호르몬과 PMS', '면역력의 출발점', '주의! 질 세정제',
    '루나컵 클래식', '루나컵 링', '루나컵 쇼티', '안전한 월경컵 선택 체크리스트',
}
H3N = {ns(h): h for h in H3}

END_PUNCT = tuple('.!?”"』」)…~:')

def slug(s, used):
    base = re.sub(r'[^\w가-힣]+', '-', s).strip('-')[:40] or 'sec'
    s2, i = base, 2
    while s2 in used:
        s2 = f'{base}-{i}'; i += 1
    used.add(s2)
    return s2

used = set()
book = []
for cid, ctitle, a, b in CHAPTERS:
    ch = {'id': cid, 'title': ctitle, 'sections': []}
    sec = None
    def new_sec(title, kind):
        global sec
        sec = {'id': slug(title, used), 'title': title, 'kind': kind, 'blocks': []}
        ch['sections'].append(sec)
    para = None
    expect_lead = False
    def flush():
        global para
        if para and para.strip():
            txt = re.sub(r'\s+', ' ', para).strip()
            if sec is None:
                new_sec(ctitle.split('. ', 1)[-1], 'section')
            sec['blocks'].append({'t': 'p', 'x': txt})
        para = None
    for p in range(a, b + 1):
        if p in TITLE_PAGES:
            continue
        plines = pages.get(p, [])
        for li, raw in enumerate(plines):
            s = raw.strip()
            nxt = next((q.strip() for q in plines[li + 1:] if q.strip()), '')
            if not s or s in RUNNING:
                continue
            h2 = H2.get(p, {}).get(s)
            if h2:
                flush(); new_sec(h2, 'section'); expect_lead = False; continue
            m = re.match(r'^Q ?\| ?(.+)$', s)
            if m:
                flush(); new_sec(m.group(1).strip(), 'qa'); expect_lead = True; continue
            if ns(s) in H3N and len(s) <= 20:
                flush()
                if sec is None: new_sec(ctitle.split('. ', 1)[-1], 'section')
                sec['blocks'].append({'t': 'h', 'x': H3N[ns(s)]}); continue
            if expect_lead:
                # lead answer may wrap to 2 lines
                if sec['blocks'] and sec['blocks'][-1]['t'] == 'lead' and not sec['blocks'][-1]['x'].endswith(END_PUNCT):
                    sec['blocks'][-1]['x'] += ('' if not raw.endswith(' ') else '') + s
                else:
                    sec['blocks'].append({'t': 'lead', 'x': s})
                if s.endswith(END_PUNCT):
                    expect_lead = False
                continue
            # drop tiny figure labels
            if len(s) <= 3 and not s.endswith(END_PUNCT):
                continue
            starts_item = bool(re.match(r'^(>|-|•|[①-⑩]|\d\. |\d\)|하나\.|둘\.|셋\.|넷\.|다섯\.|여섯\.)', s))
            if starts_item:
                flush()
            # short standalone title-like line at paragraph start -> sub heading
            if para is None and not starts_item and len(s) <= 22 and not s.endswith(END_PUNCT) \
                    and len(nxt) >= 26:
                if sec is None: new_sec(ctitle.split('. ', 1)[-1], 'section')
                sec['blocks'].append({'t': 'h', 'x': s}); continue
            if para is None:
                para = raw.lstrip()
                item_para = starts_item
            else:
                glue = ' ' if (item_para and not para.endswith(' ')) else ''
                para = para + glue + raw.lstrip()
            if s.endswith(END_PUNCT) or starts_item and s.endswith(END_PUNCT):
                flush()
    flush()
    book.append(ch)

# ---- 2026 수정 반영: 미니보틀 제공 중단 ----
edits = []
for ch in book:
    for sec in ch['sections'][:]:
        if sec['kind'] == 'qa' and '미니' in sec['title'] and '보틀' in sec['title']:
            ch['sections'].remove(sec); edits.append('미니보틀 Q&A 삭제'); continue
        nb = []
        skip_bottle = False
        for blk in sec['blocks']:
            x = blk['x']
            if sec['title'] == '세척하여 재사용' and ('미니보틀' in x or '미니 보틀' in x):
                if not skip_bottle:
                    nb.append({'t': 'p', 'x': '공공화장실처럼 바로 세척할 수 없는 곳에서는 깨끗한 휴지로 컵 안팎을 닦은 뒤 다시 착용하고, 세척할 수 있는 곳에서 흐르는 물로 충분히 씻어주세요.', 'edit': True})
                    edits.append('세척: 미니보틀 → 휴지 안내')
                skip_bottle = True
                continue
            if skip_bottle and sec['title'] == '세척하여 재사용' and ('힘차게 흔들어' in x or '담아 준비' in x):
                continue
            nb.append(blk)
        sec['blocks'] = nb

json.dump(book, open('book.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('edits:', edits)
tot = 0
for ch in book:
    print('##', ch['title'], len(ch['sections']))
    for s in ch['sections']:
        tot += 1
        print('   ', 'Q' if s['kind'] == 'qa' else '§', s['title'], len(s['blocks']))
print('sections', tot, 'chars', sum(len(b['x']) for c in book for s in c['sections'] for b in s['blocks']))
