"""노션 2차 수정용 추가 그림: 표지, 원본 교체 그림, 4컷 합치기, 단계별 그림"""
import pymupdf as fitz
from PIL import Image
D = '/home/claude/lunacup-book/fig2/'
U = '/mnt/user-data/uploads/20210907_인쇄용 최종/img/'
pdf = fitz.open('/mnt/user-data/uploads/20210907_인쇄용 최종/105-148더나은세상-TMI북 3쇄_20210907-176p.pdf')
def save(im, name, w=1360):
    im = im.convert('RGB')
    if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(D + name, 'JPEG', quality=82, optimize=True, progressive=True)
def clip(pg, r, name, dpi=300, w=1360):
    pix = pdf[pg - 1].get_pixmap(dpi=dpi, clip=fitz.Rect(r), alpha=False)
    save(Image.frombytes('RGB', [pix.width, pix.height], pix.samples), name, w)
save(Image.open(U + '표지/3쇄 표지_앞면.jpg'), 'cover.jpg', 900)
save(Image.open(U + '04/04_p107_01.jpg'), 'f107-a.jpg', 1100)
save(Image.open(U + '07/DSC01217.JPG'), 'f154-a.jpg', 1360)
clip(105, (75, 175, 295, 389), 'f105-q.jpg')
clip(173, (88, 140, 284, 312), 'f173-end.jpg')
for pg, rects in {118: [(91, 122, 167, 213), (200, 122, 285, 213), (89, 265, 169, 356), (209, 265, 276, 356)],
                  119: [(88, 122, 170, 213), (193, 123, 292, 212)],
                  120: [(87, 122, 171, 213), (197, 122, 288, 213)]}.items():
    for k, r in enumerate(rects):
        clip(pg, (r[0] - 2, r[1] - 2, r[2] + 2, r[3] + 2), f'f{pg}-{"abcd"[k]}.jpg', w=700)
print('ok')
clip(159, (37, 198, 343, 416), 'f159-0.jpg')
clip(121, (74, 104, 296, 380), 'f121-all.jpg')
save(Image.open(U + '07/DSC04857___2.jpg'), 'bg-brand.jpg', 1400)
save(Image.open('dl/h2.jpg'), 'bg-why.jpg', 1400)
