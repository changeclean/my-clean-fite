#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent, conservative CTR metadata repairs for existing ChangeClean pages."""
import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://clever-griffin-93819d.netlify.app"
GA_ID = "G-LHHLJVRM35"
REPORT = ROOT / "seo_ctr_updates.jsonl"
TITLE = re.compile(r"<title\b[^>]*>[\s\S]*?</title\s*>", re.I)
DESCRIPTION = re.compile(r"<meta\b(?=[^>]*\bname\s*=\s*['\"]?description\b)[^>]*>", re.I)
CANONICAL = re.compile(r"<link\b(?=[^>]*\brel\s*=\s*['\"]?canonical\b)[^>]*>", re.I)
HEAD_OPEN = re.compile(r"<head\b[^>]*>", re.I)
SKIP = {".git", ".github", "assets", "images", "node_modules", "__pycache__", "_recovery_test"}
SERVICE_START = re.compile(r"^(.*?)\s+(입주청소|이사청소|원룸청소|아파트청소|특수청소|거주청소|준공청소|사무실청소|상가청소|오피스텔청소|빌라청소)(.*)$")
GA_SNIPPET = f'''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>'''


def landing_metadata(document: str):
    """Use existing title only: no fabricated reviews, prices, or service promises."""
    tag = TITLE.search(document)
    if not tag:
        return None
    old = html.unescape(re.sub(r"</?title\b[^>]*>", "", tag.group(), flags=re.I)).strip()
    name = re.sub(r"\s*[|｜].*$", "", old).replace("체인지클린", "").strip()
    m = SERVICE_START.match(name)
    if not m:
        return None
    location, service, suffix = m.groups()
    if not (2 <= len(location) <= 32):
        return None
    combined = service + suffix
    if "입주청소" in combined and "이사청소" in combined:
        category = "입주청소·이사청소"
    elif "원룸청소" in combined:
        category = "원룸·오피스텔 청소" if "오피스텔" in combined else "원룸청소"
    elif "아파트청소" in combined:
        category = "아파트·빌라 청소" if "빌라" in combined else "아파트청소"
    elif "특수청소" in combined:
        category = "특수·폐기물 청소" if "폐기물" in combined else "특수청소"
    else:
        category = service
    new_title = f"{location} {category} | 작업 범위·견적 - 체인지클린"
    desc = f"{location} {category} 상담 전 알아둘 청소 범위, 견적 확인사항과 추가 작업 조건을 안내합니다. 체인지클린 서비스와 문의 방법을 확인하세요."
    if len(new_title) > 75:
        return None
    return new_title, desc


def preferred(path: Path):
    part = str(path.relative_to(ROOT))
    return (0 if re.search(r"incheon|gyeong-po-|bucheon|goyang|ilsan", part) else 1, part)


def candidate_paths():
    # Original regional landing pages first; keep main site index untouched.
    folders = [p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP and not p.name.startswith('.')]
    landing = [p / "index.html" for p in folders if p.name.endswith("-cleaning") and (p / "index.html").is_file()]
    yield from sorted(landing, key=preferred)
    # Existing child pages are eligible for missing GA4 repair only.
    for folder in sorted(folders, key=preferred):
        if not folder.name.endswith("-cleaning"):
            continue
        board = folder / "cleaning-company"
        if board.is_dir():
            yield from sorted(board.rglob("index.html"), key=preferred)


def improve(path: Path, document: str, landing: bool):
    if not HEAD_OPEN.search(document) or not TITLE.search(document):
        return document, []
    updated, changes = document, []
    extra = []
    if landing:
        info = landing_metadata(document)
        if info:
            title, desc = info
            old_title = html.unescape(re.sub(r"</?title\b[^>]*>", "", TITLE.search(updated).group(), flags=re.I)).strip()
            if old_title != title:
                updated = TITLE.sub("<title>" + html.escape(title) + "</title>", updated, count=1)
                changes.append("title")
            if not DESCRIPTION.search(updated):
                extra.append(f'<meta name="description" content="{html.escape(desc, quote=True)}">')
                changes.append("description")
            if not CANONICAL.search(updated):
                url = SITE + "/" + path.parent.relative_to(ROOT).as_posix() + "/"
                extra.append(f'<link rel="canonical" href="{html.escape(url, quote=True)}">')
                changes.append("canonical")
    if GA_ID not in updated and "googletagmanager.com/gtag/js" not in updated:
        extra.append(GA_SNIPPET)
        changes.append("ga4")
    if extra:
        updated = HEAD_OPEN.sub(lambda m: m.group() + "\n" + "\n".join(extra) + "\n", updated, count=1)
    return updated, changes


def run(limit: int, dry_run: bool):
    count, stats, records = 0, {}, []
    for path in candidate_paths():
        if count >= limit:
            break
        if path.is_symlink() or path.stat().st_size > 2_000_000:
            continue
        original = path.read_text(encoding="utf-8", errors="replace")
        landing = path.parent.parent == ROOT
        edited, changes = improve(path, original, landing)
        if not changes or edited == original:
            continue
        if not dry_run:
            path.write_text(edited, encoding="utf-8", newline="\n")
        count += 1
        for change in changes:
            stats[change] = stats.get(change, 0) + 1
        records.append({"path":path.relative_to(ROOT).as_posix(), "changes":changes})
    print(json.dumps({"dry_run":dry_run,"modified":count,"changes":stats,"sample":records[:8]},ensure_ascii=False,indent=2))
    if not dry_run and records:
        with REPORT.open("a",encoding="utf-8") as out:
            out.write(json.dumps({"run_at":datetime.now(timezone.utc).isoformat(),"modified":count,"changes":stats,"files":records},ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",type=int,default=1000)
    parser.add_argument("--dry-run",action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("limit must be between 1 and 1000")
    run(args.limit,args.dry_run)
