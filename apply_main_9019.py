# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(".")
MARKER = "<!-- MAIN_PRICE_11000_V1 -->"

OG_IMAGE = "https://clever-griffin-93819d.netlify.app/assets/cleaning-ai/clean_before_after_001.webp"

price_box = f'''
{MARKER}
<div style="
    max-width:760px;
    margin:22px auto;
    padding:18px 22px;
    background:#eef7ff;
    border-left:5px solid #0864cf;
    border-radius:12px;
    font-size:20px;
    font-weight:800;
    line-height:1.6;
    box-sizing:border-box;
">
입주청소 가격 <strong>평당 11,000원</strong><br>
<span style="font-size:14px;font-weight:500;">
현장 구조 및 오염도에 따라 최종 견적은 달라질 수 있습니다.
</span>
</div>
'''

targets = []

# 정확한 지역 메인만 찾기
for p in ROOT.rglob("index.html"):

    # 프로젝트 루트/지역폴더/index.html 형태만 허용
    try:
        rel = p.relative_to(ROOT)
    except ValueError:
        continue

    # 예: gyeong-ansan-xxx/index.html = parts 2개
    if len(rel.parts) != 2:
        continue
    try:
        s = p.read_text(encoding="utf-8")
    except:
        continue

    if "우리 지역 청소업체찾기" in s:
        targets.append(p)

print("적용 대상:", len(targets), "개")

# 안전장치
if len(targets) != 9019:
    raise SystemExit(
        f"중단: 예상 대상은 9019개인데 실제 {len(targets)}개입니다."
    )

changed = 0
already = 0
errors = 0

for i, p in enumerate(targets, 1):

    try:
        s = p.read_text(encoding="utf-8")

        # 이미 적용된 경우 중복 방지
        if MARKER in s:
            already += 1
            continue

        # ----------------------------
        # TITLE
        # ----------------------------
        m = re.search(r"<title>(.*?)</title>", s, re.I | re.S)

        if m:
            old_title = m.group(1).strip()

            if "평당 11,000원" not in old_title:
                new_title = old_title + " | 입주청소 평당 11,000원"

                s = (
                    s[:m.start(1)]
                    + new_title
                    + s[m.end(1):]
                )

        # ----------------------------
        # META DESCRIPTION
        # ----------------------------
        desc = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\'][^>]*>',
            s,
            re.I
        )

        if desc:
            old_desc = desc.group(1)

            if "평당 11,000원" not in old_desc:
                new_desc = (
                    old_desc.rstrip()
                    + " 입주청소 기본요금 평당 11,000원부터 안내합니다."
                )

                s = (
                    s[:desc.start(1)]
                    + new_desc
                    + s[desc.end(1):]
                )

        # ----------------------------
        # OG IMAGE
        # ----------------------------
        og = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]*>',
            s,
            re.I
        )

        if og:
            s = (
                s[:og.start()]
                + f'<meta property="og:image" content="{OG_IMAGE}">'
                + s[og.end():]
            )
        else:
            head = re.search(r"</head\s*>", s, re.I)

            if head:
                meta = (
                    f'\n<meta property="og:image" content="{OG_IMAGE}">\n'
                    f'<meta name="twitter:card" content="summary_large_image">\n'
                    f'<meta name="twitter:image" content="{OG_IMAGE}">\n'
                )

                s = s[:head.start()] + meta + s[head.start():]

        # ----------------------------
        # 화면 가격박스
        # H1 바로 뒤에 추가
        # ----------------------------
        h1 = re.search(r"</h1\s*>", s, re.I)

        if not h1:
            print("H1 없음:", p)
            errors += 1
            continue

        pos = h1.end()

        s = s[:pos] + price_box + s[pos:]

        # 마지막에만 파일 저장
        p.write_text(s, encoding="utf-8")

        changed += 1

    except Exception as e:
        errors += 1
        print("오류:", p, e)

    if i % 500 == 0:
        print(
            f"[{i}/9019] "
            f"완료 {changed} / "
            f"기존 {already} / "
            f"오류 {errors}",
            flush=True
        )

print()
print("===== 완료 =====")
print("대상:", len(targets))
print("수정:", changed)
print("기존:", already)
print("오류:", errors)