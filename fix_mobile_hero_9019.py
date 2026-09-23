# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(".")
PRICE_MARKER = "<!-- MAIN_PRICE_11000_V1 -->"
ROLL_MARKER = "<!-- MAIN_LIVE_ROLLING_V1 -->"

targets = []

# 루트 바로 아래 지역폴더/index.html 만 검사
for d in ROOT.iterdir():
    if not d.is_dir():
        continue

    p = d / "index.html"

    if not p.exists():
        continue

    try:
        s = p.read_text(encoding="utf-8")
    except Exception:
        continue

    # 이번에 작업한 메인만
    if (
        PRICE_MARKER in s
        and ROLL_MARKER in s
        and "우리 지역 청소업체찾기" in s
    ):
        targets.append(p)

print("대상:", len(targets), "개")

# 안전장치
if len(targets) != 9019:
    raise SystemExit(
        f"중단: 예상 9019개 / 실제 {len(targets)}개"
    )

changed = 0
already = 0
errors = 0

for i, p in enumerate(targets, 1):

    try:
        s = p.read_text(encoding="utf-8")
        original = s

        # PC hero 고정높이 해제
        s = re.sub(
            r'(\.hero-section\s*\{[^{}]*?)height\s*:\s*60vh\s*;',
            r'\1min-height:60vh; height:auto;',
            s,
            count=1,
            flags=re.I | re.S
        )

        # 모바일 hero 고정높이 해제
        s = re.sub(
            r'\.hero-section\s*\{\s*height\s*:\s*50vh\s*;\s*\}',
            '.hero-section { min-height:50vh; height:auto; padding-top:35px; padding-bottom:35px; }',
            s,
            count=1,
            flags=re.I
        )

        if s == original:
            # 테스트한 1페이지처럼 이미 수정된 경우
            if (
                "min-height:60vh; height:auto;" in s
                and "min-height:50vh; height:auto;" in s
            ):
                already += 1
            else:
                errors += 1
                print("수정 패턴 없음:", p)
            continue

        p.write_text(s, encoding="utf-8")
        changed += 1

    except Exception as e:
        errors += 1
        print("오류:", p, e)

    if i % 500 == 0:
        print(
            f"[{i}/9019] "
            f"수정 {changed} / "
            f"이미정상 {already} / "
            f"오류 {errors}",
            flush=True
        )

print()
print("===== 완료 =====")
print("대상:", len(targets))
print("수정:", changed)
print("이미정상:", already)
print("오류:", errors)