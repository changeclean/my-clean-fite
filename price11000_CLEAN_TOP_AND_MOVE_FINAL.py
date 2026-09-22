# -*- coding: utf-8 -*-
from pathlib import Path
import argparse,re,shutil

ROOT=Path.cwd()
BLOCK=r'''
<!-- PRICE11000_AFTER_IMAGES_START -->
<section class="cc-price11000" style="max-width:800px;margin:34px auto;padding:0 18px;box-sizing:border-box;text-align:center;">
<div style="background:#f3f8ff;border:1px solid #d9e9fb;border-radius:18px;padding:25px 20px;box-shadow:0 8px 24px rgba(0,0,0,.06);">
<div style="font-size:15px;font-weight:800;color:#1769c2;">체인지클린 입주청소 예상비용</div>
<div style="font-size:30px;font-weight:900;margin:6px 0 18px;">입주청소 평당 11,000원</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
<div style="background:#fff;border-radius:12px;padding:15px 5px;"><b>25평</b><br><strong>275,000원</strong></div>
<div style="background:#fff;border-radius:12px;padding:15px 5px;"><b>34평</b><br><strong>374,000원</strong></div>
<div style="background:#fff;border-radius:12px;padding:15px 5px;"><b>40평</b><br><strong>440,000원</strong></div>
</div>
<p style="font-size:13px;color:#666;margin:14px 0 0;">※ 현장 상태·구조·오염도·추가 작업에 따라 최종 견적은 달라질 수 있습니다.</p>
<a href="#estimate" style="display:inline-block;margin-top:17px;background:#ffd21c;color:#111;text-decoration:none;font-weight:900;border-radius:10px;padding:13px 20px;">⚡ 빠른 견적문의</a>
</div></section>
<!-- PRICE11000_AFTER_IMAGES_END -->
'''

def remove_price_blocks(s):
    # All marker-based price blocks made in our previous tests.
    markers=[
      ("PRICE11000_AFTER_IMAGES_START","PRICE11000_AFTER_IMAGES_END"),
      ("PRICE11000_BODY_START","PRICE11000_BODY_END")
    ]
    for a,b in markers:
        s=re.sub(r'<!--\s*'+a+r'\s*-->.*?<!--\s*'+b+r'\s*-->','',s,flags=re.I|re.S)

    # Remove the earlier unmarked top price card by its unique heading + price text.
    # It was inserted as a section containing both these phrases.
    while True:
        hit=re.search(r'<section\b[^>]*>.*?체인지클린 입주청소 예상비용.*?입주청소 평당 11,000원.*?</section>',s,re.I|re.S)
        if not hit: break
        s=s[:hit.start()]+s[hit.end():]
    return s

def patch(p):
    original=p.read_text(encoding="utf-8",errors="replace")
    s=remove_price_blocks(original)

    # Real supplied page anchor: content-images M2/M3/M4/M6 group.
    m=re.search(r'<div\s+class=["\']content-images["\'][^>]*>.*?</div>',s,re.I|re.S)
    if not m: return False,"content-images 못 찾음"
    if "입주청소" not in s[:50000]: return False,"입주청소 페이지 아님"

    s=s[:m.end()]+"\n"+BLOCK+s[m.end():]

    # Existing form becomes the target for fast estimate, without moving it.
    if 'id="estimate"' not in s:
        s=re.sub(r'(<section\b[^>]*class=["\'][^"\']*form-container[^"\']*["\'])',
                 r'\1 id="estimate"',s,count=1,flags=re.I)

    # Literal backslash-n artifacts from old patch attempts.
    s=re.sub(r'(?m)^\s*\\n\s*$','',s)

    bak=p.with_suffix(p.suffix+".before_price_cleanup.bak")
    if not bak.exists(): shutil.copy2(p,bak)
    p.write_text(s,encoding="utf-8")
    return True,"수정 성공"

ap=argparse.ArgumentParser()
ap.add_argument("--test",required=True)
a=ap.parse_args()
p=ROOT/a.test
if not p.exists(): raise SystemExit("파일 없음: "+str(p))
ok,msg=patch(p)
final=p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""
print("결과:",msg)
print("가격표 마커:",final.count("PRICE11000_AFTER_IMAGES_START"),"개")
print("평당 11,000원 문구:",final.count("입주청소 평당 11,000원"),"개")
print("위치: content-images 바로 다음")
