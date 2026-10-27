"""세로로 쌓인 단계 그림(f108, f109)을 칸별로 잘라 f108-s1.jpg … 로 저장"""
from PIL import Image
import numpy as np
D = '/home/claude/lunacup-book/fig2/'
for name in ('f108-0', 'f109-0'):
    im = Image.open(D + name + '.jpg').convert('RGB')
    a = np.asarray(im.convert('L'))
    blank = (a > 235).mean(axis=1) > 0.985
    runs, start = [], None
    for y, bl in enumerate(blank):
        if not bl and start is None: start = y
        if bl and start is not None:
            if y - start > 40: runs.append((start, y))
            start = None
    if start is not None and len(a) - start > 40: runs.append((start, len(a)))
    print(name, im.size, runs)
    for k, (y0, y1) in enumerate(runs, 1):
        im.crop((0, max(0, y0 - 6), im.width, min(im.height, y1 + 6))).save(D + f'{name[:4]}-s{k}.jpg', quality=82)
