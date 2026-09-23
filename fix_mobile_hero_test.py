# -*- coding: utf-8 -*-
from pathlib import Path
import re

# 방금 확인했던 테스트 페이지
p = Path(r".\gyeong-goyang-ilsanseo-ilsan-cheong-ra-cleaning\index.html")

if not p.exists():
    raise SystemExit(f"파일을 찾을 수 없습니다: {p}")

s = p.read_text(encoding="utf-8")

if "<!-- MAIN_LIVE_ROLLING_V1 -->" not in s:
    raise SystemExit("중단: 이 페이지에는 롤링박스가 없습니다.")

original = s

# PC hero
s = re.sub(
    r'(\.hero-section\s*\{[^{}]*?)height\s*:\s*60vh\s*;',
    r'\1min-height:60vh; height:auto;',
    s,
    count=1,
    flags=re.I | re.S
)

# 모바일 hero
s = re.sub(
    r'\.hero-section\s*\{\s*height\s*:\s*50vh\s*;\s*\}',
    '.hero-section { min-height:50vh; height:auto; padding-top:35px; padding-bottom:35px; }',
    s,
    count=1,
    flags=re.I
)

if s == original:
    raise SystemExit("중단: 수정할 hero 높이 코드를 찾지 못했습니다.")

p.write_text(s, encoding="utf-8")

print("===== 테스트 수정 완료 =====")
print(p)
print("11,000원 박스: 유지")
print("롤링박스: 유지")
print("hero 고정높이: 해제")