# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, re, shutil

ROOT=Path.cwd()
START="<!-- PRICE11000_AFTER_IMAGES_START -->"
END="<!-- PRICE11000_AFTER_IMAGES_END -->"

BLOCK=r"""
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
"""

def patch(p):
    s=p.read_text(encoding="utf-8",errors="replace")
    # Remove only our prior price blocks from failed tests.
    s=re.sub(re.escape(START)+r".*?"+re.escape(END),"",s,flags=re.S)
    s=re.sub(r'<!-- PRICE11000_BODY_START -->.*?<!-- PRICE11000_BODY_END -->',"",s,flags=re.S)

    # Actual supplied main-page structure:
    # 지역업체찾기 banner -> <div class="content-images"> ... </div> -> feedback/body
    m=re.search(r'<div\s+class=["\']content-images["\'][^>]*>.*?</div>',s,re.I|re.S)
    if not m:
        return False,"content-images 못 찾음"

    # Only price pages containing move-in cleaning language.
    if "입주청소" not in s[:50000]:
        return False,"입주청소 페이지 아님"

    pos=m.end()
    new=s[:pos]+"\n"+BLOCK+s[pos:]

    # Give fast button a reliable target without moving any existing sections.
    if 'id="estimate"' not in new:
        new=re.sub(r'(<section\b[^>]*class=["\'][^"\']*form-container[^"\']*["\'])',
                   r'\1 id="estimate"',new,count=1,flags=re.I)

    if new==s: return False,"변경 없음"
    bak=p.with_suffix(p.suffix+".before_price_after_images.bak")
    if not bak.exists(): shutil.copy2(p,bak)
    p.write_text(new,encoding="utf-8")
    return True,"수정 성공"

ap=argparse.ArgumentParser()
ap.add_argument("--test",required=True)
a=ap.parse_args()
p=ROOT/a.test
if not p.exists():
    raise SystemExit("파일 없음: "+str(p))
ok,msg=patch(p)
print("결과:",msg)
print("삽입위치: content-images 닫힘 바로 다음")
print("상단 hero / 실시간 견적문의 / 지역 청소업체찾기: 수정하지 않음")
