# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, re, shutil

ROOT = Path.cwd()
START = "<!-- PRICE11000_BODY_START -->"
END = "<!-- PRICE11000_BODY_END -->"

BLOCK = """
<!-- PRICE11000_BODY_START -->
<section style="max-width:780px;margin:36px auto;padding:0 18px;box-sizing:border-box;">
<div style="background:#f3f8ff;border:1px solid #d9e9fb;border-radius:18px;padding:26px 22px;text-align:center;">
<div style="font-size:15px;font-weight:700;color:#1769c2;margin-bottom:7px;">체인지클린 입주청소 예상비용</div>
<div style="font-size:30px;font-weight:900;margin-bottom:20px;">입주청소 평당 11,000원</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
<div style="background:#fff;border-radius:12px;padding:16px 6px;"><b>25평</b><br><strong>275,000원</strong></div>
<div style="background:#fff;border-radius:12px;padding:16px 6px;"><b>34평</b><br><strong>374,000원</strong></div>
<div style="background:#fff;border-radius:12px;padding:16px 6px;"><b>40평</b><br><strong>440,000원</strong></div>
</div>
<div style="font-size:13px;color:#666;margin-top:15px;">※ 현장 상태, 구조, 오염도 및 추가 작업에 따라 최종 견적은 달라질 수 있습니다.</div>
<div style="margin-top:18px;"><a href="tel:01068113176" style="display:inline-block;background:#126fd1;color:#fff;text-decoration:none;font-weight:800;border-radius:10px;padding:13px 18px;margin:4px;">상담직통 010-6811-3176</a><a href="tel:01068113176" style="display:inline-block;background:#ffd21c;color:#222;text-decoration:none;font-weight:900;border-radius:10px;padding:13px 18px;margin:4px;">⚡ 빠른 견적문의</a></div>
</div>
</section>
<!-- PRICE11000_BODY_END -->
"""

def process(p):
    s = p.read_text(encoding="utf-8", errors="replace")
    path = str(p).lower().replace(chr(92), "/")
    if "/cleaning-company/" in path or "입주청소" not in s[:50000]:
        return False
    s = re.sub(re.escape(START)+r".*?"+re.escape(END), "", s, flags=re.S)
    # 본문 제목 직전에만 삽입. 상단 hero/실시간견적/지역업체찾기에는 삽입하지 않음.
    anchors = [
        r"<h2[^>]*>\s*청소\s*전\s*확인할\s*부분\s*</h2>",
        r"<h2[^>]*>[^<]*청소\s*범위[^<]*</h2>"
    ]
    pos = None
    for pat in anchors:
        m = re.search(pat, s, flags=re.I)
        if m:
            pos = m.start()
            break
    if pos is None:
        return False
    new = s[:pos] + BLOCK + "\n" + s[pos:]
    bak = p.with_suffix(p.suffix + ".before_price11000_body.bak")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_text(new, encoding="utf-8")
    return True

ap = argparse.ArgumentParser()
ap.add_argument("--test")
args = ap.parse_args()
if args.test:
    p = ROOT / args.test
    print("결과:", "수정 성공" if p.exists() and process(p) else "수정 안 됨")
    print("상단 유지 / 본문에 평당 11,000원 삽입")
else:
    files = list(ROOT.rglob("index.html"))
    changed = 0
    for p in files:
        if process(p):
            changed += 1
            if changed % 250 == 0: print("수정", changed)
    print("완료: 검사", len(files), "/ 수정", changed)
