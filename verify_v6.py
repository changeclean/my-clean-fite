# -*- coding: utf-8 -*-
"""
verify_v6.py

V6 SEO 사이트 전체 검증 엔진

검사 항목
- deploys 폴더 내 개별 페이지 검사
- {{...}} 템플릿 토큰 잔존 여부
- title 누락 여부
- meta description 누락 여부
- canonical 누락 여부
- h1 누락 여부
- JSON-LD 기본 형식 검사
- 이미지 src 누락/로컬 파일 존재 여부
- 내부 링크 href 검사
- sitemap.xml 정상 XML 여부
- robots.txt 정상 여부
- rss.xml 정상 여부

실행:
    python verify_v6.py

빠른 테스트:
    python verify_v6.py --limit 100

결과:
    verify_report_v6.csv
    verify_summary_v6.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent
DEPLOYS_DIR = BASE_DIR / "deploys"

REPORT_CSV = BASE_DIR / "verify_report_v6.csv"
SUMMARY_TXT = BASE_DIR / "verify_summary_v6.txt"

SITE_URL = "https://changeclean1.netlify.app"

SKIP_DIRS = {
    "region",
    "service",
    "regions",
    "services",
    "category",
    "images",
    "assets",
    "css",
    "js",
    "__pycache__",
}


@dataclass
class PageCheck:
    slug: str
    path: str
    status: str
    has_template_token: bool
    missing_title: bool
    missing_description: bool
    missing_canonical: bool
    missing_h1: bool
    jsonld_error: bool
    missing_local_images: int
    suspicious_links: int
    message: str


def clean(value) -> str:
    return "" if value is None else str(value).strip()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def find_page_files() -> List[Path]:
    files = []
    if not DEPLOYS_DIR.exists():
        return files

    for folder in sorted(DEPLOYS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name in SKIP_DIRS:
            continue

        index_file = folder / "index.html"
        if index_file.exists():
            files.append(index_file)

    return files


def has_template_token(html: str) -> bool:
    return bool(re.search(r"{{[^{}]+}}", html))


def missing_title(html: str) -> bool:
    m = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if not m:
        return True
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    return not title


def missing_description(html: str) -> bool:
    m = re.search(r'<meta\s+name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, flags=re.I | re.S)
    if not m:
        # content가 앞에 있고 name이 뒤에 있는 경우도 보정
        m = re.search(r'<meta\s+[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', html, flags=re.I | re.S)
    if not m:
        return True
    return len(clean(m.group(1))) < 20


def missing_canonical(html: str) -> bool:
    m = re.search(r'<link\s+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, flags=re.I | re.S)
    if not m:
        m = re.search(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html, flags=re.I | re.S)
    if not m:
        return True
    href = clean(m.group(1))
    return not href.startswith("http")


def missing_h1(html: str) -> bool:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    if not m:
        return True
    text = re.sub(r"<[^>]+>", "", m.group(1))
    text = re.sub(r"\s+", " ", text).strip()
    return not text


def jsonld_error(html: str) -> bool:
    blocks = re.findall(
        r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    )

    if not blocks:
        return False  # 없는 것은 오류로 보지 않음. 별도 정책 가능.

    for block in blocks:
        text = block.strip()
        if not text:
            return True
        try:
            json.loads(text)
        except Exception:
            return True

    return False


def local_image_missing_count(html: str) -> int:
    srcs = re.findall(r'<img\s+[^>]*src=["\']([^"\']+)["\']', html, flags=re.I)
    missing = 0

    for src in srcs:
        src = clean(src)

        if not src:
            missing += 1
            continue

        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            continue

        if src.startswith("/"):
            local_path = DEPLOYS_DIR / src.lstrip("/")
        else:
            local_path = DEPLOYS_DIR / src

        if not local_path.exists():
            missing += 1

    return missing


def suspicious_link_count(html: str) -> int:
    hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, flags=re.I)
    bad = 0

    for href in hrefs:
        href = clean(href)

        if not href:
            bad += 1
            continue

        if href.startswith("#") or href.startswith("tel:") or href.startswith("mailto:"):
            continue

        if href.startswith("http://") or href.startswith("https://"):
            continue

        # 내부 링크
        if href.startswith("/"):
            parts = [p for p in href.strip("/").split("/") if p]
            if not parts:
                continue

            # sitemap, rss, robots 같은 파일
            if parts[0].endswith(".xml") or parts[0].endswith(".txt"):
                target = DEPLOYS_DIR / parts[0]
                if not target.exists():
                    bad += 1
                continue

            target = DEPLOYS_DIR.joinpath(*parts)
            if target.is_dir():
                target = target / "index.html"

            if not target.exists():
                bad += 1

    return bad


def check_page(path: Path) -> PageCheck:
    slug = path.parent.name
    try:
        html = read_text(path)

        token = has_template_token(html)
        mt = missing_title(html)
        md = missing_description(html)
        mc = missing_canonical(html)
        mh = missing_h1(html)
        je = jsonld_error(html)
        mi = local_image_missing_count(html)
        sl = suspicious_link_count(html)

        problems = []
        if token:
            problems.append("template_token")
        if mt:
            problems.append("missing_title")
        if md:
            problems.append("missing_description")
        if mc:
            problems.append("missing_canonical")
        if mh:
            problems.append("missing_h1")
        if je:
            problems.append("jsonld_error")
        if mi:
            problems.append(f"missing_images:{mi}")
        if sl:
            problems.append(f"suspicious_links:{sl}")

        status = "OK" if not problems else "WARN"

        return PageCheck(
            slug=slug,
            path=str(path),
            status=status,
            has_template_token=token,
            missing_title=mt,
            missing_description=md,
            missing_canonical=mc,
            missing_h1=mh,
            jsonld_error=je,
            missing_local_images=mi,
            suspicious_links=sl,
            message="; ".join(problems),
        )

    except Exception as e:
        return PageCheck(
            slug=slug,
            path=str(path),
            status="ERROR",
            has_template_token=False,
            missing_title=True,
            missing_description=True,
            missing_canonical=True,
            missing_h1=True,
            jsonld_error=True,
            missing_local_images=0,
            suspicious_links=0,
            message=str(e),
        )


def check_xml_file(path: Path, expected_root_keywords: List[str]) -> Tuple[bool, str]:
    if not path.exists():
        return False, f"{path.name} 없음"

    text = read_text(path)[:300]

    if not text.startswith("<?xml"):
        return False, f"{path.name} XML 선언 없음"

    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        return False, f"{path.name} XML 파싱 오류: {e}"

    tag = root.tag.lower()
    if expected_root_keywords and not any(k.lower() in tag for k in expected_root_keywords):
        return False, f"{path.name} 루트 태그 이상: {root.tag}"

    return True, f"{path.name} 정상"


def check_robots() -> Tuple[bool, str]:
    path = DEPLOYS_DIR / "robots.txt"
    if not path.exists():
        return False, "robots.txt 없음"

    text = read_text(path)
    if "Sitemap:" not in text:
        return False, "robots.txt에 Sitemap 없음"

    if "Disallow: /" in text:
        return False, "robots.txt가 전체 차단 가능성"

    return True, "robots.txt 정상"


def write_report(results: List[PageCheck]) -> None:
    fields = list(asdict(results[0]).keys()) if results else [
        "slug", "path", "status", "has_template_token", "missing_title",
        "missing_description", "missing_canonical", "missing_h1",
        "jsonld_error", "missing_local_images", "suspicious_links", "message"
    ]

    with open(REPORT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))


def write_summary(results: List[PageCheck], sitemap_status: Tuple[bool, str], rss_status: Tuple[bool, str], robots_status: Tuple[bool, str]) -> None:
    total = len(results)
    ok = sum(1 for r in results if r.status == "OK")
    warn = sum(1 for r in results if r.status == "WARN")
    error = sum(1 for r in results if r.status == "ERROR")

    token_count = sum(1 for r in results if r.has_template_token)
    title_count = sum(1 for r in results if r.missing_title)
    desc_count = sum(1 for r in results if r.missing_description)
    canon_count = sum(1 for r in results if r.missing_canonical)
    h1_count = sum(1 for r in results if r.missing_h1)
    jsonld_count = sum(1 for r in results if r.jsonld_error)
    image_missing_total = sum(r.missing_local_images for r in results)
    suspicious_link_total = sum(r.suspicious_links for r in results)

    # 점수
    penalty = (
        token_count * 5
        + title_count * 3
        + desc_count * 3
        + canon_count * 3
        + h1_count * 2
        + jsonld_count * 2
        + min(image_missing_total, 500) * 0.2
        + min(suspicious_link_total, 500) * 0.2
    )
    score = max(0, 100 - (penalty / max(total, 1)))

    lines = []
    lines.append("V6 SEO 검증 리포트")
    lines.append("=" * 40)
    lines.append(f"검사일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"검사 페이지 수: {total}")
    lines.append("")
    lines.append(f"정상 OK: {ok}")
    lines.append(f"경고 WARN: {warn}")
    lines.append(f"오류 ERROR: {error}")
    lines.append("")
    lines.append("문제 요약")
    lines.append("-" * 40)
    lines.append(f"템플릿 토큰 잔존 페이지: {token_count}")
    lines.append(f"Title 누락: {title_count}")
    lines.append(f"Description 누락/짧음: {desc_count}")
    lines.append(f"Canonical 누락: {canon_count}")
    lines.append(f"H1 누락: {h1_count}")
    lines.append(f"JSON-LD 오류: {jsonld_count}")
    lines.append(f"누락 이미지 총합: {image_missing_total}")
    lines.append(f"의심 내부링크 총합: {suspicious_link_total}")
    lines.append("")
    lines.append("사이트 파일")
    lines.append("-" * 40)
    lines.append(sitemap_status[1])
    lines.append(rss_status[1])
    lines.append(robots_status[1])
    lines.append("")
    lines.append(f"최종 점수: {score:.1f} / 100")
    lines.append("")
    lines.append(f"상세 리포트: {REPORT_CSV.name}")

    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="V6 전체 사이트 검증")
    parser.add_argument("--limit", type=int, default=0, help="앞에서 N개만 검사")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    files = find_page_files()

    if args.limit:
        files = files[:args.limit]

    if not files:
        print("검사할 페이지가 없습니다. deploys 폴더를 확인하세요.")
        return 1

    print(f"검사 시작: {len(files)}개 페이지")

    results = []
    for i, path in enumerate(files, start=1):
        results.append(check_page(path))
        if i % 1000 == 0:
            print(f"진행: {i}/{len(files)}")

    sitemap_status = check_xml_file(DEPLOYS_DIR / "sitemap.xml", ["sitemapindex"])
    rss_status = check_xml_file(DEPLOYS_DIR / "rss.xml", ["rss"])
    robots_status = check_robots()

    write_report(results)
    write_summary(results, sitemap_status, rss_status, robots_status)

    # 심각 조건
    severe = any([
        sum(1 for r in results if r.has_template_token) > 0,
        not sitemap_status[0],
        not robots_status[0],
    ])

    return 2 if severe else 0


if __name__ == "__main__":
    raise SystemExit(main())
