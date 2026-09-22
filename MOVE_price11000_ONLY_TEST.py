# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, re, shutil

ROOT = Path.cwd()
START = "<!-- PRICE11000_MOVE_START -->"
END = "<!-- PRICE11000_MOVE_END -->"

def find_price_block(s):
    # Find the exact existing price card by unique text, then expand only to its nearest enclosing section.
    needle = "입주청소 평당 11,000원"
    idx = s.find(needle)
    if idx < 0:
        return None

    # Ignore SEO occurrences in <head>; use the first occurrence after <body>.
    body = re.search(r"<body\b[^>]*>", s, re.I)
    if body:
        idx = s.find(needle, body.end())
    if idx < 0:
        return None

    # Existing card is a section. Find nearest opening section before text and its matching closing section.
    starts = list(re.finditer(r"<section\b[^>]*>", s[:idx], re.I))
    if not starts:
        return None
    st = starts[-1].start()

    # Token-count section nesting from this opening tag.
    token_re = re.compile(r"<section\b[^>]*>|</section\s*>", re.I)
    depth = 0
    for m in token_re.finditer(s, st):
        tok = m.group(0).lower()
        if tok.startswith("<section") and not tok.startswith("</"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                en = m.end()
                block = s[st:en]
                if needle in block:
                    return st, en, block
                return None
    return None

def patch(p):
    s = p.read_text(encoding="utf-8", errors="replace")

    # If a prior successful MOVE marker exists, remove marker only so rerun remains safe.
    s = s.replace(START, "").replace(END, "")

    found = find_price_block(s)
    if not found:
        return False, "화면 가격표 블록 못 찾음"
    st, en, block = found

    # Safety: never move hero/live estimate/local-company banner.
    forbidden = ["hero-section", "CHANGE_CLEAN_LIVE_ESTIMATE", "우리 지역 청소업체찾기", "content-images"]
    bad = [x for x in forbidden if x in block]
    if bad:
        return False, "안전중단: 가격표 블록에 다른 영역 포함 -> " + ", ".join(bad)

    # Remove exactly that existing block only.
    without = s[:st] + s[en:]

    # Find the actual existing image group after removal.
    m = re.search(r'<div\s+class=["\']content-images["\'][^>]*>.*?</div>', without, re.I | re.S)
    if not m:
        return False, "content-images 못 찾음"

    moved = "\n" + START + "\n" + block + "\n" + END + "\n"
    new = without[:m.end()] + moved + without[m.end():]

    # Structural safety checks before writing.
    checks = {
        "hero-section": len(re.findall(r'hero-section', new, re.I)),
        "live-estimate": len(re.findall(r'CHANGE_CLEAN_LIVE_ESTIMATE', new, re.I)),
        "local-banner": new.count("우리 지역 청소업체찾기"),
        "content-images": len(re.findall(r'class=["\']content-images["\']', new, re.I)),
        "move-marker": new.count(START),
    }
    if checks["hero-section"] < 1 or checks["live-estimate"] < 1 or checks["local-banner"] < 1 or checks["content-images"] < 1 or checks["move-marker"] != 1:
        return False, "안전중단: 구조검사 실패 " + str(checks)

    bak = p.with_suffix(p.suffix + ".before_MOVE_price11000.bak")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_text(new, encoding="utf-8")
    return True, checks

ap = argparse.ArgumentParser()
ap.add_argument("--test", required=True)
a = ap.parse_args()
p = ROOT / a.test
if not p.exists():
    raise SystemExit("파일 없음: " + str(p))

ok, info = patch(p)
print("결과:", "MOVE 성공" if ok else info)
if ok:
    print("구조검사:", info)
    print("작업: 기존 가격표 HTML만 content-images 바로 뒤로 이동")
    print("Hero / 실시간 견적문의 / 지역업체찾기 / 이미지: 보존")
