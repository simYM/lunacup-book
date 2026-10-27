"""노션 '웹북 수정' 요청과 PDF 원고 대조로 찾은 오류를 섹션별로 직접 바로잡기"""
import re

BASE = None


def N(s):
    return re.sub(r'[^0-9A-Za-z가-힣]', '', s)


def sec(b, title):
    for c in b:
        for s in c['sections']:
            if s['title'].rstrip('.').startswith(title.rstrip('.')):
                return s
    raise KeyError(title)


def find(s, key, t=None, start=0):
    """key: 글 앞부분(정규화 비교) 또는 그림 이름(f000-0)"""
    for i, x in enumerate(s['blocks']):
        if i < start: continue
        if t and x['t'] != t: continue
        v = x['x']
        if re.fullmatch(r'f\d{3}-\d', key):
            if x['t'] == 'img' and v.endswith(key + '.jpg'): return i
            continue
        if isinstance(v, str) and N(v).startswith(N(key)): return i
    raise KeyError(f"{s['title']} :: {key}")


def has(s, key):
    try:
        find(s, key); return True
    except KeyError:
        return False


def pop(s, key, t=None):
    return s['blocks'].pop(find(s, key, t))


def drop(s, *keys):
    for k in keys:
        if has(s, k): pop(s, k)


def IMG(name, alt=''):
    return {'t': 'img', 'x': BASE + name + '.jpg', 'alt': alt}


def PAIR(a, b):
    return {'t': 'imgs', 'x': [BASE + a + '.jpg', BASE + b + '.jpg']}


def P(x, **kw): return dict({'t': 'p', 'x': x}, **kw)
def H(x, cls='blue'): return {'t': 'h', 'x': x, 'cls': cls}
def CAP(x): return {'t': 'cap', 'x': x}
def BTN(*pairs): return {'t': 'btns', 'x': list(pairs)}
def GRID(*items): return {'t': 'grid', 'x': [dict(it, img=BASE + it['img'] + '.jpg') for it in items]}


def after(s, key, *blocks):
    i = find(s, key) + 1
    s['blocks'][i:i] = list(blocks)


def before(s, key, *blocks):
    i = find(s, key)
    s['blocks'][i:i] = list(blocks)


def settext(s, key, text, **kw):
    x = s['blocks'][find(s, key)]
    x['x'] = text; x.pop('marks', None); x.update(kw)
    return x


def apply(b, ST):
    global BASE
    for c in b:
        for s in c['sections']:
            for x in s['blocks']:
                if x['t'] == 'img':
                    BASE = x['x'].rsplit('/', 1)[0] + '/'; break
            if BASE: break
        if BASE: break

    # ── 들어가는 글: 제목 + 마지막 삽화
    s = sec(b, '들어가는 글')
    s['title'] = '월경컵 입문자를 위한 응원가'
    x = s['blocks'][find(s, '편리해서')]
    x['x'] = x['x'].replace('편리해서,안전해서,경제적이라,친환경적이라,', '편리해서, 안전해서, 경제적이라, 친환경적이라, '); x.pop('marks', None)
    s['blocks'].append(IMG('f012-0', '월경은 재채기처럼 숨길 수 없다. 단 한 방울도 흘리지 않겠다는 엄격함에서 해방되자!'))

    # ── 거울로 만나는 외음부
    s = sec(b, '거울로 만나는 외음부')
    pop(s, '음핵(클리토리스: Clitoris)')
    settext(s, '음핵', '음핵(클리토리스: Clitoris)')
    s['blocks'] = [x for i, x in enumerate(s['blocks']) if not (x['t'] == 'h' and x['x'] == '질 입구와 질 막')]
    f27 = pop(s, 'f027-0')
    after(s, '질 막은 질 바로 안쪽에', f27)

    # ── 신비로운 내성기: 그림 설명이 본문에 섞인 곳
    s = sec(b, '신비로운 내성기')
    x = s['blocks'][find(s, '포궁은 스스로 호르몬과')]
    x['x'] = x['x'].replace('포궁은 모든 것을 희생포궁과 골반에 연결된 인대하며 생명을', '포궁은 모든 것을 희생하며 생명을'); x.pop('marks', None)

    # ── 내 몸의 리듬, 월경
    s = sec(b, '내 몸의 리듬, 월경')
    drop(s, '뇌하수체호르몬의 양호르몬의', '에스트로겐 프로게스테론황체')
    i = find(s, '포궁에서 배출된 월경혈은')
    s['blocks'][i] = P('포궁에서 배출된 월경혈은 주름이 많은 질 벽을 타고 흘러내린다. 질 벽은 아코디언 주름처럼 생겨서 월경혈이 천천히 흐르게 된다. 월경이 막 시작된 1~2일에는 양이 많기 때문에 배출되는 흐름도 빠르고 월경혈도 선홍색의 신선한 색이다. 하지만 3~4일로 접어들면 흐름이 느려지고 질 벽에 머물다 배출되는 경우도 있기 때문에 월경혈의 색도 갈색을 띠게 된다.')
    pop(s, '- 혈색은 선홍색')
    pop(s, 'f044-0'); pop(s, 'f045-0')
    after(s, '포궁에서 배출된 월경혈은', CAP('평균 월경량(80ml)의 사용자의 월경컵 사용 일지'), PAIR('f044-0', 'f045-0'))
    # 월경 혐오 말풍선 + NO 그림을 한 그림처럼
    pop(s, 'f047-0')
    i = find(s, 'f046-0'); s['blocks'][i] = PAIR('f046-0', 'f047-0')
    # 월경통 박스 줄 나누기
    i = find(s, '원발성 월경통: 골반')
    bx = s['blocks'][i]['box']
    s['blocks'][i:i + 1] = [P('원발성 월경통: 골반 장기에 이상 증상 없이 나타나는 월경통', box=bx, cls='green'),
                            P('속발성 월경통: 골반 장기의 이상에 의해 나타나는 월경통', box=bx, cls='green'),
                            P('원인: 포궁내막증, 난관염, 골반염, 포궁 내 장치, 포궁선근종, 포궁내 폴립, 포궁기형, 포궁흡착 등등', box=bx, cls='green')]
    # 소제목 중복
    s['blocks'] = [x for x in s['blocks'] if not (x['t'] == 'p' and x['x'] == '월경통, 참지말고 미리 챙기자!')]
    # 진통제 표: 그림 안에 표와 주의 문구가 다 들어 있음
    drop(s, '아랫배가 살살 아픈', '* 카페인 성분이', '평소 카페인에 민감한')
    s['blocks'] = [x for x in s['blocks'] if not (x['t'] == 'cap' and '통증 1단계' in x['x'])]
    # 호르몬 인용 박스를 본문에서 떼어 그림 아래로
    i = find(s, '월경전증후군(PMS)이라는 말은')
    x = s['blocks'][i]
    head, _, _ = x['x'].partition('호르몬 hormone')
    nxt = s['blocks'][i + 1]
    x['x'] = head + '한 결과를 찾지 못했다. PMS를 겪고 있는 여성들의 혈액 검사에서 일반적으로 비정상이라고 판단할만한 호르몬 비율이 나타나지 않았기 때문이다.'
    x['x'] = x['x'].replace('명백한 결과', '명백한 결과')
    x.pop('marks', None)
    if nxt['x'].startswith('한 결과를 찾지 못했다'): s['blocks'].pop(i + 1)
    f54 = pop(s, 'f054-0')
    after(s, 'f051-0', P("호르몬 hormone'이란 단어는 그리스어로 '나는 자극한다'를 뜻한다. 몸속 기관들을 자극하는 능력에서 유래한 이름이다.",
                         box=['hormone', 'green'], cls='green'))
    drop(s, '일회용생리대를 생산하기')
    s['blocks'].append(f54)

    # ── 월경컵 연대기
    s = sec(b, '월경컵 연대기')
    after(s, 'f057-0', CAP('리오나 차머스가 미국 특허청에 접수한 실제 문서'))

    # ── 월경컵 소재와 구조
    s = sec(b, '월경컵 소재와 구조')
    s['blocks'] = [
        P('리오나 차머스가 세상에 선보인 월경컵은 고무로 만들어졌다. 이제 고무로 만든 월경컵은 더 이상 생산되지 않지만 오늘날 월경컵의 소재는 더 다양해졌다.'),
        IMG('f060-0', '키퍼(The Keeper) 라텍스 고무, 메루나(meLuna) 열가소성 엘라스토머(TPE), 루나컵(LunaCup) 의료용 실리콘, 합성 실리콘'),
        P('의료용 실리콘, 합성 라텍스, 열가소성 엘라스토머(TPE), 유연한 합성 폴리머등으로 다양하다. 이 가운데 가장 안전한 소재는 의료용 실리콘이다. 의료용 실리콘은 체내 이식에 적합한 소재로 개발되어 장시간 체내에 머물러도 안심할 수 있다.'),
        P('열가소성 엘라스토머(TPE) 소재는 플라스틱의 한 종류로 아직 안전성 논란에서 자유롭지 않다. 제작사는 현재까지 어떤 위험도 증명되지 않았다고 하지만, 유연한 플라스틱일수록 가소성을 높이기 위해 첨가하는 물질이 많은 것은 잘 알려진 사실이다.'),
        IMG('f061-0', '월경컵의 구조: 손잡이(꼬리), 미끄럼 방지선, 공기구멍(숨구멍), 입구 링'),
        P('국내에서 식약처 허가를 받고 유통되는 월경컵은 모두 반투명한 흰색 컬러의 월경컵이다. 흰색 월경컵은 1년 이상 사용하게 되면 착색과 변색에 더 취약할 수밖에 없는데, 이 때문에 컬러 월경컵을 만들어 달라는 요청이 많았다.'),
        P('우리는 실제로 제품 개발을 위해 소재의 안전성 시험을 진행했다. 그러나 그 과정에서 컬러 소재의 위험 가능성을 알게 되었고, 중도 포기라는 쉽지 않은 결정을 내려야만 했다.'),
        P('제품 개발을 중도에 포기하기는 쉽지 않은 결정이었다. 하지만 소비자 입장에서 생각해보니 답은 명확했다.'),
        s['blocks'][find(s, '우리가 컬러 월경컵 개발을 포기한')],
    ]

    # ── 월경컵의 경도와 탄성
    s = sec(b, '월경컵의 경도와 탄성')
    f67 = pop(s, 'f067-0')
    pop(s, 'f063-0')
    drop(s, '간단한 탄성 체크법')
    i = find(s, '월경컵이 작동하는 원리는')
    s['blocks'][i:i + 2] = [P('월경컵이 작동하는 원리는 질 내벽과 월경컵 입구가 밀착(실링)하여 월경혈이 새지 않도록 모아서 처리하는 것이다. 우리 몸은 계속 움직이기 때문에 사용자가 어떤 동작을 해도 몸 안에 월경컵이 이물감 없이 자연스럽게 모양을 유지할 수 있는 것이 중요하다. 이때 너무 단단하면 방광을 압박하거나 이물감으로 불편할 수 있고, 탄성이 없으면 몸의 움직임을 바로바로 따라오지 못해서 질 벽과 빈틈이 생기고 월경혈이 샐 수 있다.'),
                            P('월경컵 입문자에게 부드러운 월경컵을 권하는 이유가 하나 더 있다. 단단한 월경컵은 몸의 움직임이나 변화에 대응하지 못하고 몸 안에서 단단하게 버티고 있기 때문에 방광을 압박하거나 배변을 불편하게 할 수 있기 때문이다. 쪼그려 앉거나 배에 힘을 주면 질 내부는 그 힘에 눌리게 되는데 부드럽고 탄성이 좋은 월경컵은 질 모양에 따라 눌렸다가도 빠르게 복원이 되는 반면, 단단한 월경컵은 단단하게 버티고 있어 불편하고 심하면 통증이 생기기도 한다. 단단한 월경컵을 선택한 월경컵 입문자 중에서 이런 이유로 중도에 포기하는 경우가 많은데 격렬한 운동을 자주하는 경우가 아니라면 부드러운 경도의 월경컵을 선택하는 것이 좋다. 또, 운동을 즐기지만 압박감과 불편함 때문에 월경컵 선택이 어려웠다면, 부드러운 월경컵을 사용하되 자주 비워주면 간단히 해결할 수 있다.')]
    pop(s, '입문자 중에서 이런 이유로')
    s['blocks'] += [IMG('f063-0', '간단한 탄성 체크법'),
                    CAP('간단한 탄성 체크법: 월경컵을 반 접어서 30초간 손에 꼭 쥐고 있다가 펴줍니다. 손을 폈을 때 바로 원래의 모습으로 돌아오지 못하고 찌그러진 상태라면 새것으로 교체해 주세요.')]

    # ── 월경컵에 도전하는 우리의 자세
    s = sec(b, '월경컵에 도전하는 우리의 자세')
    i = find(s, '처음 월경컵을 착용하고 불편하다면')
    s['blocks'][i] = P('처음 월경컵을 착용하고 불편하다면 바로 제거하자. 그리고 차츰 착용 시간을 늘려보자. 첫날 1시간 착용했다면 다음날 2시간으로 늘리고 다음 날 불편하지 않다면 4시간, 5시간 이렇게 차츰 늘려가다 보면 어느덧 월경컵 사용에 익숙해진 자신을 발견할 수 있을 것이다.')
    pop(s, '착용 시간을 늘려보자')
    after(s, '처음 월경컵을 착용하고 불편하다면', IMG('f067-0', '도전! 입문단계, 적응단계, 마스터단계'),
          CAP('입문단계: 내 몸에 월경컵을 소개하는 시기로 절대 무리하지 말고 천천히 사용 시간을 늘려가자!'),
          CAP('적응단계: 착용과 제거를 손에 익히는 시기로 나만의 사용 노하우를 찾아보자!'),
          CAP('마스터단계: 사용에 완전히 적응한 시기로 월경량과 활동량에 따라 맞는 월경컵을 선택해 사용해보자!'))

    # ── 나에게 맞는 월경컵은?
    s = sec(b, '나에게 맞는 월경컵은')
    s['blocks'] = [x for x in s['blocks'] if not (x['t'] == 'p' and x['x'] == '두께가 얇고, 입구 모양이 단순한 것')]
    drop(s, '경도: 2.5 부드러워요탄성: 5', '경도: 2.5 부드러워요탄성: 5')
    i = find(s, '처음에는 착용에서 느껴지는 감각이')
    s['blocks'][i] = P('처음에는 착용에서 느껴지는 감각이 예민하기 때문에 작은 불편도 크게 느껴진다. 되도록 작은 크기의 월경컵으로 3~4주기 사용 후, 어느 정도 익숙해졌다면 좀 더 큰 크기의 월경컵으로 도전하자.')
    pop(s, '도 크게 느껴진다')
    f71 = pop(s, 'f071-0')
    after(s, '처음에는 착용에서 느껴지는 감각이', f71)
    # 체크리스트 박스는 '안전한 월경컵 선택법' 본문 다음으로
    boxblk = [x for x in s['blocks'] if x.get('box') and x['box'][1] == 'green']
    s['blocks'] = [x for x in s['blocks'] if x not in boxblk]
    after(s, '월경컵은 체내에 직접 사용하는 제품이기', *boxblk)

    # ── 질 길이가 잴 때마다 달라요: [포궁] 링크
    s = sec(b, '질 길이가 잴 때 마다 달라요')
    x = s['blocks'][find(s, '앞에 [포궁]부분에서')]
    x['link'] = ('[포궁]', '#lcb-a-pogung')
    s0 = sec(b, '신비로운 내성기')
    s0['blocks'][next(i for i, y in enumerate(s0['blocks']) if y['t'] == 'h' and y['x'] == '포궁')]['anchor'] = 'lcb-a-pogung'

    # ── 성경험이 없어도: 초록 강조 답과 일반 문장 분리
    s = sec(b, '성경험이 없어도 사용할 수 있나요')
    i = find(s, '월경컵은 성 경험의 여부와')
    s['blocks'][i:i + 1] = [{'t': 'lead', 'x': '월경컵은 성 경험의 여부와 상관없이 사용하실 수 있습니다.', 'cls': 'green'},
                            P('많은 분이 월경컵 사용을 성 경험과 연관 지어 고민합니다.')]

    # ── 월경컵, 아프지 않나요?: 반신욕 그림은 출산경험 Q 끝으로, 무료 교육 QR 삭제
    s = sec(b, '월경컵, 아프지 않나요')
    f82 = pop(s, 'f082-0')
    s2 = sec(b, '출산경험이 있는데 새지 않을까요')
    s2['blocks'] = [x for x in s2['blocks'] if not (x['t'] == 'cap' and '무료 월경교육' in x['x'])]
    s2['blocks'].append(f82)

    # ── 접기: 소제목 → 설명(본문) → 그림
    s = sec(b, '접기')
    s['blocks'] = [
        H('라비아 접기'), P('가장 작게 접을 수 있지만 연습이 필요한 접기 방법입니다.'), IMG('f084-0', '라비아 접기 1~4단계'),
        H('하프다이아 접기'), P('접는 데 힘은 많이 들지만 펴지는 힘이 가장 강한 접기 방법입니다.'), IMG('f085-0', '하프다이아 접기 1~4단계'),
        H('펀치다운 접기'), P('가장 쉬운 접기 방법이지만 펴졌는지 꼭 확인이 필요해요.'), IMG('f086-0', '펀치다운 접기 1~4단계'),
        H('C자 접기'), P('접기는 쉽지만 처음 도전에는 불편할 수 있어요.'), IMG('f087-0', 'C자 접기 1~2단계'),
        IMG('f087-1', '월경컵의 다양한 접기 방법을 영상으로 확인하세요.'),
    ]
    # ── 착용하기
    s = sec(b, '착용하기')
    s['blocks'] = [
        H('준비자세'), IMG('f088-0', '월경컵 착용 준비자세'),
        H('넣기'), IMG('f089-0', '넣기 1~4단계'),
        H('펴주고 실링(진공) 확인하기'),
        H('월경컵 펴주기', 'blue'),
        P('월경컵의 밑 부분을 빙 둘려 만졌을 때 접히거나 구겨진 곳이 없으면 잘 펴진 것입니다. 질 내부의 공간은 개인의 차가 있어 월경컵이 납작하게 눌려 자리를 잡기도 합니다.'),
        IMG('f090-1', '월경컵 밑 부분을 빙 둘러 만졌을 때, 굴곡이 없으면 잘 펴진 것이다.'),
        IMG('f090-0', '월경컵 밑부분을 잡고 컵을 회전하거나, 움직여주면 굴곡이 펴진다.'),
        P('접히거나 구겨진 곳이 있으면 컵의 밑 부분을 잡고 돌려주거나, 위아래로 흔들어 주면 자연스럽게 펴집니다.'),
        H('실링(진공) 확인 요령'),
        P("월경컵 입구와 질 벽이 밀착되는 것을 '실링'이라고 합니다.", cls='bold'),
        P('실링이 잘 되면 꼬리를 잡아당겼을 때 바로 빠지지 않고 버티는 힘이 느껴집니다. 월경컵 꼬리가 한쪽으로 치우쳐 소음순을 자극하지 않도록 잘 위치해 주세요.'),
        IMG('f091-0', '실링 확인'),
    ]

    # ── 아프고 불편해요
    s = sec(b, '아프고 불편해요')
    i = find(s, '뇌는 이 자극이 위험한 것인지')
    s['blocks'][i]['x'] = s['blocks'][i]['x'].replace('자놀라지마!', '자') + s['blocks'][i + 2]['x']
    s['blocks'][i].pop('marks', None)
    f92 = s['blocks'].pop(i + 1); s['blocks'].pop(i + 1)
    after(s, '아프다면 참지 말고', f92)
    f94 = pop(s, 'f094-0')
    after(s, '질은 뒤쪽으로 45도', f94)

    # ── 자꾸 소변이 마려워요
    s = sec(b, '자꾸 소변이 마려워요')
    f95 = pop(s, 'f095-0')
    i = find(s, '2~3주기 정도 지나도')
    s['blocks'][i]['x'] = '월경컵을 처음 사용한다면 익숙하지 않아 불편할 수 있어요. ' + s['blocks'][i]['x']
    s['blocks'].append(f95)

    # ── 넣기 전에 펴져요
    s = sec(b, '넣기 전에 펴져요')
    i = find(s, '월경컵을 한 손으로 넣기가')
    s['blocks'][i:i + 2] = [P('월경컵을 한 손으로 넣기가 어렵다면 양손을 사용해주세요. 한 손으로 월경컵을 단단히 잡고 다른 손으로 월경컵의 밑부분을 부드럽게 밀어줍니다.')]

    # ── 꼬리가 거슬려요
    s = sec(b, '꼬리가 거슬려요')
    x = s['blocks'][find(s, '막대기형 꼬리를')]
    x['x'] = x['x'].replace('꼬리를 자월경컵 입구 실링이안된 경우르기로', '꼬리를 자르기로'); x.pop('marks', None)

    # ── 샜어요: 영상 QR 그림 설명 중복
    s = sec(b, '샜어요')
    drop(s, '월경컵의 실링을 영상으로')

    # ── 얼마나 자주 비워야 하나요
    s = sec(b, '얼마나 자주 비워야 하나요')
    f113 = pop(s, 'f113-0')
    i = find(s, '보통의 경우 월경량은')
    s['blocks'][i]['x'] = '월경량은 호르몬의 양에 따라 개인마다 다르기 때문에, 나에게 맞는 시간을 찾아야 합니다. ' + s['blocks'][i]['x']
    after(s, '월경량은 호르몬의 양에 따라', f113)

    # ── 갈색 피가 보여요: 일차별 그림과 박스는 이 질문에 속함
    s = sec(b, '배변할 때 빠지기도 하나요')
    moved = [x for x in s['blocks'] if (x['t'] == 'img' and x['x'].endswith('f134-0.jpg')) or x.get('box')]
    s['blocks'] = [x for x in s['blocks'] if x not in moved]
    sec(b, '갈색 피가 보여요')['blocks'].extend(moved)

    # ── 독성쇼크증후군: 손씻기 손글씨는 그림 안에
    s = sec(b, '독성쇼크증후군이 의심돼요')
    drop(s, '월경컵 사용 전30초 손씻기')

    # ── 브랜드 페이지 글자는 그림 안에 다 있음
    s = sec(b, 'LUNACUP STORY')
    drop(s, 'SINCE 2018, FROM KOREA')

    # ── 분류 배출: 손글씨는 그림 안에
    s = sec(b, '월경컵은 어떻게 분류 배출하나요')
    drop(s, '당신은 아름답고 강하다')

    # ── 왜, 루나컵을 선택하나요: 붙어버린 목록 줄 나누기
    s = sec(b, '왜, 루나컵을 선택하나요')
    i = find(s, '의료용 실리콘 100%한국과')
    s['blocks'][i:i + 1] = [P('의료용 실리콘 100%'), P('한국과 미국 식약처 허가'), P('CE(유럽) & ISO 13485:2016(국제) 의료등급 생산관리 인증')]

    # ── 월경 그리고 혐오: 붙어버린 소제목
    s = sec(b, '월경 그리고 혐오')
    i = find(s, "I'm not sorry. I'm menstruating")
    s['blocks'][i:i + 1] = [H("I'm not sorry. I'm menstruating", 'purple'),
                            P(s['blocks'][i]['x'].split('menstruating', 1)[1])]

    # ── 월경, 그 무한한 가능성: 끊어진 문단
    s = sec(b, '월경, 그 무한한 가능성')
    i = find(s, '2007년에 일본 연구자')
    s['blocks'][i]['x'] += s['blocks'][i + 1]['x']; s['blocks'][i].pop('marks', None)
    s['blocks'].pop(i + 1)

    # ── 건조해서 보관: 네 단계 그림을 순서대로 2×2
    s = sec(b, '건조해서 보관')
    s['blocks'] = [x for x in s['blocks'] if x['t'] != 'img'] + [PAIR('f121-0', 'f121-1'), PAIR('f121-2', 'f121-3')]

    # ── 비우고 교체하기: 단계 그림 옆에 설명
    s = sec(b, '비우고 교체하기')
    st = [('f108-s1', '1. 손 씻기', '비누를 사용해서 꼼꼼히 씻는다.'),
          ('f108-s2', '2. 실링 해제', '월경컵의 밑 부분을 꼬집듯이 잡아 비틀어 준다. 월경컵과 질 내부에 공기가 들어가 실링이 해제되면 부드럽게 꺼낸다.'),
          ('f108-s3', '3. 혈 비우기', '혈이 튀지 않게 조심스럽게 흘려 보낸다.'),
          ('f109-s1', '4. 월경컵 세척', '착색을 예방하기 위해 찬물에 깨끗이 씻는다.'),
          ('f109-s2', '5. 다시 착용', '물기를 털어 다시 착용한다.'),
          ('f109-s3', '6. 펴주고 실링 확인', '월경컵이 잘 펴졌는지 확인한다.')]
    s['blocks'] = [H('월경컵 교체하는 방법'),
                   {'t': 'isteps', 'x': [{'img': BASE + f + '.jpg', 'title': t, 'text': d} for f, t, d in st]}]

    # ══ 3차 노션 수정 ══
    # 한자
    s = sec(b, '자궁 vs 포궁')
    for x in s['blocks']:
        if isinstance(x['x'], str) and ('丒' in x['x'] or '剏' in x['x']):
            x['x'] = x['x'].replace('丒', '子').replace('剏', '胞'); x.pop('marks', None)
    # 나에게 맞는 월경컵 찾기 버튼
    s = sec(b, '나에게 맞는 월경컵은')
    after(s, 'f072-0', BTN(('나에게 맞는 생리컵 찾기', 'https://lunacup.co.kr/choice')))
    # 샜어요: 실링이 안 된 경우 소제목 + 4컷 한 그림, 영상 QR 대신 버튼
    s = sec(b, '샜어요')
    drop(s, 'f105-0', 'f105-1', 'f106-1')
    before(s, '자신에게 맞는 컵인지 또는', H('실링이 안 된 경우'))
    after(s, '자신의 질보다 작거나', IMG('f105-q', '실링이 안 된 경우 네 가지 예'))
    s['blocks'] += [IMG('f107-a', '영상으로 알아보기'),
                    BTN(('월경컵의 실링을 영상으로 알아보기', 'https://www.youtube.com/watch?v=YJO8HDxWfDc'),
                        ('월경컵 실링 해제법을 영상으로 알아보기', 'https://www.youtube.com/watch?v=Vwb5eX4vbvY'))]
    # 뺄 때 아파요: 부항기 · 숨구멍 나란히
    s = sec(b, '뺄 때 아파요')
    drop(s, 'f111-0', 'f111-1')
    s['blocks'].append(PAIR('f111-0', 'f111-1'))
    # 열탕 소독: 제목은 글자로, 그림과 설명 따로
    s = sec(b, '사용 전, 사용 후 열탕 소독')
    box = [x for x in s['blocks'] if x.get('box')]
    s['blocks'] = [H('끓인 물에 열탕 소독하기'),
                   GRID({'img': 'f118-a', 'text': ['① 월경컵이 충분히 잠길만한 큰 머그잔을 준비한 후, 깨끗이 씻은 월경컵을 넣어 주세요.']},
                        {'img': 'f118-b', 'text': ['② 전기주전자에 충분한 물을 끓여주세요.']},
                        {'img': 'f118-c', 'text': ['③ 80~100℃의 끓은 물을 월경컵이 충분히 잠길 정도로 머그잔에 붓고 5분간 열탕 소독합니다.']},
                        {'img': 'f118-d', 'text': ['④ 완전히 건조한 후 통풍이 되는 파우치나 미니보틀에 보관해주세요.']}),
                   GRID({'title': '냄비에 열탕 소독하기', 'img': 'f119-a', 'text': ['① 냄비에 물을 충분히 넣고 끓인다.', '② 물이 끓으면 월경컵이 냄비에 직접 닿지 않게 주의하여 3분간 끓인다.', '③ 완전히 건조하여 보관한다.']},
                        {'title': '전자레인지에 열탕 소독하기', 'img': 'f119-b', 'text': ['① 전자레인지 사용이 가능한 용기에 월경컵을 넣는다.', '② 월경컵이 충분히 물에 잠기도록 용기에 물을 넣는다.', '③ 전자레인지에 1분 30초간 가열하여 열탕 소독한다.', '④ 전자레인지에서 꺼내 5분간 놓아둔다.', '⑤ 5분 후 물을 버리고 월경컵을 꺼내 완전히 건조하여 보관한다.']})] + box
    # 세척하여 재사용: 미니보틀 사용 예 되살리기
    s = sec(b, '세척하여 재사용')
    box = [x for x in s['blocks'] if x.get('box')]
    s['blocks'] = [GRID({'title': '세면대에서 세척할 경우', 'img': 'f120-a', 'text': ['흐르는 깨끗한 물에 충분히 씻어주세요.']},
                        {'title': '미니 보틀 사용의 예', 'img': 'f120-b', 'text': ['권장하는 재사용 방법은 흐르는 물에 충분히 세척하여 착용하는 것입니다. 하지만 공공화장실에서 바로 세척할 수 없는 상황이라면 미니보틀을 이용하여 세척하세요.', '월경컵을 교체할 때 미니보틀에 물을 담아 준비합니다. 혈을 비운 후 미니보틀에 넣고 뚜껑을 꼭 닫습니다. 힘차게 흔들어 세척한 다음 꺼내서 물기를 닦은 후 착용하세요.']}),
                   {'t': 'h', 'x': '주의!', 'cls': 'pink', 'box': box[0]['box']}] + box
    # 건조해서 보관: 그림 먼저, 설명은 그림 아래
    s = sec(b, '건조해서 보관')
    s['blocks'] = [x for x in s['blocks'] if x['t'] == 'imgs'] + [x for x in s['blocks'] if x['t'] != 'imgs']
    # 새 월경컵 교체 그림은 '언제 새 월경컵으로 바꾸나요' 끝으로
    s = sec(b, '월경컵에서 이상한 냄새가 나요')
    f130 = pop(s, 'f130-0')
    sec(b, '언제 새 월경컵으로 바꾸나요')['blocks'].append(f130)
    # 미니 보틀도 열탕 소독해요? 되살리기 (냄새 Q 다음)
    for c in b:
        for k, s2 in enumerate(c['sections']):
            if s2 is s:
                c['sections'].insert(k + 1, {'title': '미니 보틀도 열탕 소독해요?', 'kind': 'qa', 'blocks': [
                    {'t': 'lead', 'x': '열탕 소독 없이, 깨끗이 세척하여 사용하시는 것만으로 충분합니다.', 'cls': 'green'},
                    P('루나컵과 함께 드리는 미니보틀은 열탕에도 환경호르몬과 유해물질이 용출되지 않는 BPA free, 트라이탄 소재로 안전하지만 상대적으로 열에 약한 특성이 있어 장기간 열에 노출될 경우 변형될 수 있습니다. 루나컵 보관과 세척을 위해 미니보틀을 사용하는 경우 반드시 열탕소독이 필요하지 않으며, 깨끗이 세척하여 사용하는 것으로 충분합니다. 열탕소독을 원하시는 경우 직접 끓이는 방법보다 끓인 물 80~100℃의 물을 담아 5분간 담가 소독해주세요.'),
                    {'t': 'h', 'x': '미니보틀 사용할 때 다음을 주의해주세요.', 'cls': 'pink', 'box': ['mini', 'grey']},
                    P('> 열탕 소독할 경우 직접 끓이지 말고 중탕해주세요.', cls='pink', box=['mini', 'grey']),
                    P('> 전자레인지에 사용하실 경우 물을 가득 담아 중탕하시고, 1분 30초를 넘기지 마세요.', cls='pink', box=['mini', 'grey']),
                    P('> 직접 열에 닿지 않도록 주의해주세요.', cls='pink', box=['mini', 'grey'])]})
                break
    # 신수증 X-ray 출처 버튼
    s = sec(b, '월경컵, 부작용은 없나요')
    after(s, 'f147-0', BTN(('출처 바로가기', 'https://radiopaedia.org/cases/menstrual-cup-device')))
    # 분류 배출: 그림은 본문 끝
    s = sec(b, '월경컵은 어떻게 분류 배출하나요')
    for c in b:
        for s3 in c['sections']:
            s3['blocks'] = [x for x in s3['blocks'] if not (x['t'] == 'img' and x['x'].endswith('f150-0.jpg'))]
    s['blocks'].append(IMG('f150-0', '당신은 아름답고 강하다!'))
    # 브랜드: I'M NOT SORRY 바로 밑에 '월경, 숨기지 마!', 교육 사진 교체
    s = sec(b, 'LUNACUP STORY')
    sub = pop(s, '월경, 숨기지 마')
    after(s, "I’M NOT SORRY", sub)
    i = find(s, 'f154-0'); s['blocks'][i] = IMG('f154-a', '루나컵 월경교육 현장')
    # 책 마지막 그림
    b[-1]['sections'][-1]['blocks'].append(IMG('f173-end', "당신의 '열정'을 응원합니다. 건강한 월경문화를 위해 루나컵과 함께 해주세요."))

    # ══ 4차 노션 수정 ══
    s = sec(b, '접기')
    after(s, 'f087-1', BTN(('월경컵 접는 방법 영상 보기', 'https://www.youtube.com/watch?v=F58Y_Gzwd_M')))
    s = sec(b, '건조해서 보관')
    s['blocks'] = [IMG('f121-all', '월경 시작·월경 중·월경 끝·보관')] + [x for x in s['blocks'] if x['t'] != 'imgs']
    for c in b:
        c['sections'] = [x for x in c['sections'] if not x['title'].startswith('미니 보틀도 열탕')]
    s = sec(b, '독성쇼크증후군이 의심돼요')
    i = find(s, '‘독성쇼크증후군’(TSS)을 예방하는')
    bx = s['blocks'][i + 1]['box']
    s['blocks'][i]['box'] = bx; s['blocks'][i].pop('cls', None)
    s['blocks'][i + 1].pop('cls', None)
    s['blocks'][i + 2].pop('cls', None); s['blocks'][i + 2]['cls'] = 'src'
    s = sec(b, 'LUNACUP STORY')
    s['blocks'] = [x for x in s['blocks'] if not (x['t'] == 'img' and (x['x'].endswith('f152-0.jpg') or x['x'].endswith('f153-0.jpg') or x['x'].endswith('f155-0.jpg')))]
    s['blocks'].insert(0, {'t': 'panel', 'x': '', 'img': BASE + 'bg-brand.jpg', 'theme': 'dark', 'parts': [
        ('h', 'LUNACUP STORY: BRAND'), ('sub', 'SINCE 2018, FROM KOREA'), ('sub', '여성이 만든 여성기업'),
        ('p', '루나컵은 여성의 건강한 월경주기를 위해 2018년, 한국에서 시작되었습니다. 누구나 월경컵을 사용할 수 있도록 연구하고 개발합니다. 지금까지 루나컵은 8종의 루나컵을 만들었습니다.'),
        ('h', 'CHALLENGE IS CHANGE'), ('sub', '도전을 멈추지 말아요!'),
        ('p', '월경은 종종 신체적 한계로 인식됩니다. 월경 기간에도 자유롭게 활동하고, 꿈을 위한 도전은 계속되어야 합니다. 도전하는 여성에게 한계는 없습니다. 루나컵은 도전하는 여성들을 뜨겁게 응원합니다. 도전을 멈추지 말아요!')]})
    s = sec(b, '왜, 루나컵을 선택하나요')
    i = find(s, 'f157-0')
    s['blocks'] = [x for x in s['blocks'] if not (x['t'] == 'img' and (x['x'].endswith('f157-0.jpg') or x['x'].endswith('f158-0.jpg')))]
    s['blocks'].insert(i, {'t': 'panel', 'x': '', 'img': BASE + 'bg-why.jpg', 'theme': 'light', 'parts': [
        ('sub', '둘. 경제적이니까요.'), ('p', '모으고, 비우고, 세척하여 2년간 재사용.'),
        ('sub', '셋. 쓰레기를 만들지 않아요.'), ('p', '플라스틱과 쓰레기에서 자유로운 월경주기<br>나와 지구를 위해 가장 쉬운 행동'),
        ('sub', '넷. 도전을 계속할 수 있어요.'), ('p', '월경주기에도 원한다면 무엇이든 할 수 있어요.<br>달리기, 수영, 요가, 춤, 서핑, 자전거, 등산…'),
        ('sub', '다섯. 입문자에게 최적화된 디자인이니까요.'),
        ('ul', ['질 모양과 닮은 종 모양의 디자인', '자극을 최소화한 심플한 디자인', '이물감 없는 얇은 두께', '착용감이 좋은 부드러운 경도', '잘 펴지는 높은 탄성', '다양한 선택지의 크기와 손잡이 디자인'])]})

    # ── 공통: 박스 안 글자색 통일, 박스 제목만 굵게
    for c in b:
        for s in c['sections']:
            groups = {}
            for x in s['blocks']:
                if x.get('box'): groups.setdefault(tuple(x['box']), []).append(x)
            for k, xs in groups.items():
                cols = [x.get('cls') for x in xs if x.get('cls') and x.get('cls') != 'src']
                if cols:
                    col = max(set(cols), key=cols.count)
                    for x in xs:
                        if x.get('cls') != 'src': x['cls'] = col
                for j, x in enumerate(xs):
                    t = x['x'].strip() if isinstance(x['x'], str) else ''
                    x['boxhead'] = j == 0 and len(xs) > 1 and (x['t'] == 'h' or (len(t) <= 22 and not t.endswith(('.', '요', '다', '!'))))
