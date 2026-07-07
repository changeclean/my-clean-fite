# -*- coding: utf-8 -*-
"""
make_sites_v6_pro.py

체인지클린 template.html 전용 V6 Pro 생성 엔진

이 파일은 사용자가 제공한 현재 template.html 구조에 맞춘 전용 생성기입니다.

주요 기능
- keywords.xlsx / keywords.csv 읽기
- template.html 전체 전역 치환
- {{지역명}} 전부 치환
- {{오늘날짜}} 치환
- {{피드백}} 자동 생성
- {{FAQ}} 자동 생성
- {{페이지번호}} 내부링크 자동 생성
- title / description / canonical / schema 보강
- 이미지 경로 ../images → /images 자동 보정
- report_v5.csv 생성
- deploys/{slug}/index.html 생성
- 기존 캐시 기반 중복 재생성 방지
- --force 사용 시 전체 재생성

실행:
    python make_sites_v6_pro.py

테스트:
    python make_sites_v6_pro.py --limit 100 --force

이후:
    python deploy_v6.py --skip-keywords --no-git
    git add .
    git commit -m "make sites v6 pro"
    git push
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    import pandas as pd
except ImportError:
    pd = None


BASE_DIR = Path(__file__).resolve().parent

KEYWORD_XLSX = BASE_DIR / "keywords.xlsx"
KEYWORD_CSV = BASE_DIR / "keywords.csv"
TEMPLATE_FILE = BASE_DIR / "template.html"

OUTPUT_DIR = BASE_DIR / "deploys"
CACHE_DIR = BASE_DIR / ".cache"
LOG_DIR = BASE_DIR / "logs"

CACHE_FILE = CACHE_DIR / "page_hash_v6_pro.json"
REPORT_FILE = BASE_DIR / "report_v5.csv"

SITE_URL = "https://changeclean1.netlify.app"
BRAND_NAME = "체인지클린"
PHONE_TEXT = "빠른상담:1688-6751"
PHONE_NUMBER = "1688-6751"


@dataclass
class Page:
    index: int
    keyword: str
    slug: str
    region: str
    service: str
    category: str
    title: str
    description: str
    h1: str
    canonical: str


def clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd is not None and pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def esc(value: Any) -> str:
    text = clean(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def md5_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    text = clean(text).lower()
    text = text.replace("\\", "/").strip("/")
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9가-힣/_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = re.sub(r"/{2,}", "/", text)
    return text.strip("-/")


def infer_region(keyword: str, region: str = "") -> str:
    region = clean(region)
    if region:
        return region

    words = clean(keyword).split()
    if not words:
        return "해당 지역"

    if len(words) >= 2 and words[0] in ["서울", "경기", "인천"]:
        return f"{words[0]} {words[1]}"

    return words[0]


def infer_service(keyword: str, service: str = "") -> str:
    service = clean(service)
    if service:
        return service

    services = [
        "입주청소", "이사청소", "준공청소", "상가청소", "사무실청소",
        "빌라청소", "아파트청소", "오피스텔청소", "거주청소",
        "화장실청소", "주방청소", "유리창청소", "곰팡이청소",
        "부분청소", "특수청소", "퇴거청소"
    ]

    for item in services:
        if item in keyword:
            return item

    return "전문청소"


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    ensure_dirs()
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}_make_sites_v6_pro.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_cache() -> Dict[str, str]:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache: Dict[str, str]) -> None:
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def read_keywords(input_file: str = "") -> List[Page]:
    path = Path(input_file) if input_file else KEYWORD_XLSX
    if not path.is_absolute():
        path = BASE_DIR / path

    if not path.exists():
        if KEYWORD_CSV.exists():
            path = KEYWORD_CSV
        else:
            raise FileNotFoundError("keywords.xlsx 또는 keywords.csv 파일이 없습니다.")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        if pd is None:
            raise ImportError("엑셀 파일을 읽으려면 pandas/openpyxl이 필요합니다.")
        df = pd.read_excel(path).fillna("")
        rows = df.to_dict(orient="records")
    else:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

    pages: List[Page] = []
    seen_slugs = set()

    for i, row in enumerate(rows, start=1):
        keyword = clean(row.get("keyword") or row.get("키워드") or row.get("Keyword"))
        if not keyword:
            continue

        slug = slugify(row.get("slug") or row.get("Slug") or row.get("url_slug") or keyword)
        if not slug:
            continue

        base_slug = slug
        count = 2
        while slug in seen_slugs:
            slug = f"{base_slug}-{count}"
            count += 1
        seen_slugs.add(slug)

        region = infer_region(keyword, row.get("region") or row.get("지역"))
        service = infer_service(keyword, row.get("service") or row.get("서비스"))
        category = clean(row.get("category") or row.get("카테고리") or service)

        title = clean(row.get("title") or row.get("Title") or row.get("seo_title"))
        if not title:
            title = f"{keyword} | {BRAND_NAME}"

        description = clean(row.get("description") or row.get("Description") or row.get("meta_description"))
        if not description:
            description = f"{keyword} 전문업체 {BRAND_NAME}. 입주청소, 이사청소, 상가청소, 사무실청소를 현장 상황에 맞춰 꼼꼼하게 진행합니다."
        description = description[:155]

        h1 = clean(row.get("h1") or row.get("H1")) or keyword
        canonical = clean(row.get("canonical") or row.get("url")) or f"{SITE_URL.rstrip('/')}/{slug}/"

        pages.append(Page(
            index=i,
            keyword=keyword,
            slug=slug,
            region=region,
            service=service,
            category=category,
            title=title,
            description=description,
            h1=h1,
            canonical=canonical,
        ))

    return pages


def default_template() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{{지역명}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
<h1>{{지역명}}</h1>
<div>{{피드백}}</div>
<div>{{FAQ}}</div>
<div>{{페이지번호}}</div>
</body>
</html>
"""


def load_template() -> str:
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return default_template()


def build_feedback(page: Page) -> str:
    return f"""
{page.keyword} 현장은 공간 구조와 오염 상태에 따라 작업 범위가 달라질 수 있습니다.

{BRAND_NAME}은 {page.region} 지역의 {page.service} 작업에서 주방, 욕실, 창틀, 바닥, 수납장 내부처럼 고객이 실제로 확인하는 구역을 중심으로 꼼꼼하게 점검합니다.

상담 시 평수, 구조, 희망 날짜, 현장 사진을 알려주시면 더 정확한 안내가 가능합니다.
""".strip()


def build_faq(page: Page) -> str:
    faqs = [
        (
            f"{page.keyword} 작업 시간은 얼마나 걸리나요?",
            "평수, 구조, 오염도, 작업 범위에 따라 달라집니다. 상담 시 현장 정보를 알려주시면 더 정확하게 안내드립니다."
        ),
        (
            f"{page.keyword} 청소 범위는 어디까지 포함되나요?",
            "기본적으로 주방, 욕실, 창틀, 바닥, 수납장 내부 등 생활 공간 중심으로 진행합니다."
        ),
        (
            "견적 상담은 어떻게 하나요?",
            "전화 상담 또는 예약폼으로 지역, 평수, 희망 날짜를 남겨주시면 확인 후 안내드립니다."
        ),
        (
            "당일 예약도 가능한가요?",
            "일정에 여유가 있는 경우 가능하지만, 원하는 날짜가 있다면 미리 상담하는 것이 좋습니다."
        ),
    ]

    html = []
    for q, a in faqs:
        html.append(f"""
<div class="faq-item">
<h3>Q. {esc(q)}</h3>
<p>{esc(a)}</p>
</div>
""")

    return "\n".join(html)


def build_page_links(page: Page, pages: List[Page], limit: int = 40) -> str:
    scored = []

    for other in pages:
        if other.slug == page.slug:
            continue

        score = 0

        if other.region == page.region:
            score += 3

        if other.service == page.service:
            score += 2

        if score > 0:
            scored.append((score, other))

    scored.sort(key=lambda x: (-x[0], x[1].keyword))

    selected = [p for _, p in scored[:limit]]

    if len(selected) < limit:
        existing = {p.slug for p in selected}
        for other in pages:
            if other.slug == page.slug or other.slug in existing:
                continue
            selected.append(other)
            existing.add(other.slug)
            if len(selected) >= limit:
                break

    links = []
    for item in selected:
        active = " active" if item.slug == page.slug else ""
        links.append(f'<a class="{active}" href="/{esc(item.slug)}/">{esc(item.keyword)}</a>')

    return "\n".join(links)


def build_schema(page: Page) -> str:
    obj = {
        "@context": "https://schema.org/",
        "@type": "Review",
        "itemReviewed": {
            "@type": "LocalBusiness",
            "name": f"{BRAND_NAME} {page.keyword}점",
            "image": f"{SITE_URL.rstrip('/')}/images/M2.jpg",
            "telephone": PHONE_NUMBER,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "주안동 981-17",
                "addressLocality": "인천광역시 미추홀구",
                "addressRegion": "인천",
                "addressCountry": "KR",
            },
        },
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": "5",
            "bestRating": "5",
        },
        "author": {
            "@type": "Person",
            "name": "실제이용고객",
        },
        "reviewBody": f"{page.keyword} 서비스를 이용했는데, 구석구석 꼼꼼하게 작업해주셔서 새집처럼 깨끗해졌습니다. 강력 추천합니다!",
    }
    return json.dumps(obj, ensure_ascii=False, indent=2)


def replace_or_insert_head(html: str, page: Page) -> str:
    """
    기존 template.html의 title, meta description, canonical, schema를 SEO에 맞게 보강합니다.
    기존 Review JSON-LD 내부 {{지역명}}은 전역 치환으로 해결되지만,
    title/description/canonical은 확실하게 다시 맞춥니다.
    """
    if "<head" not in html.lower():
        return html

    # title은 항상 교체
    html = re.sub(r"<title>.*?</title>", f"<title>{esc(page.title)}</title>", html, flags=re.I | re.S)

    # description이 있으면 교체, 없으면 삽입
    if re.search(r'<meta\s+name=["\']description["\']', html, flags=re.I):
        html = re.sub(
            r'<meta\s+name=["\']description["\'][^>]*>',
            f'<meta name="description" content="{esc(page.description)}">',
            html,
            flags=re.I,
        )
    else:
        html = re.sub(
            r"</head>",
            f'<meta name="description" content="{esc(page.description)}">\n</head>',
            html,
            flags=re.I,
        )

    # canonical이 있으면 교체, 없으면 삽입
    if re.search(r'<link\s+rel=["\']canonical["\']', html, flags=re.I):
        html = re.sub(
            r'<link\s+rel=["\']canonical["\'][^>]*>',
            f'<link rel="canonical" href="{esc(page.canonical)}">',
            html,
            flags=re.I,
        )
    else:
        html = re.sub(
            r"</head>",
            f'<link rel="canonical" href="{esc(page.canonical)}">\n</head>',
            html,
            flags=re.I,
        )

    # OG 기본 보강
    if "og:title" not in html:
        og = f"""
<meta property="og:title" content="{esc(page.title)}">
<meta property="og:description" content="{esc(page.description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(page.canonical)}">
"""
        html = re.sub(r"</head>", og + "\n</head>", html, flags=re.I)

    return html


def render_page(page: Page, pages: List[Page], template: str) -> str:
    replacements = {
        "{{지역명}}": page.keyword,
        "{{오늘날짜}}": datetime.now().strftime("%Y.%m.%d"),
        "{{피드백}}": build_feedback(page),
        "{{FAQ}}": build_faq(page),
        "{{페이지번호}}": build_page_links(page, pages),
        "{{TITLE}}": page.title,
        "{{DESCRIPTION}}": page.description,
        "{{H1}}": page.h1,
        "{{CANONICAL}}": page.canonical,
        "{{KEYWORD}}": page.keyword,
        "{{REGION}}": page.region,
        "{{SERVICE}}": page.service,
        "{{CATEGORY}}": page.category,
        "{{BRAND_NAME}}": BRAND_NAME,
        "{{PHONE_TEXT}}": PHONE_TEXT,
        "{{PHONE_NUMBER}}": PHONE_NUMBER,
        "{{SCHEMA}}": build_schema(page),
    }

    html = template

    # 현재 템플릿 전체 전역 치환
    for token, value in replacements.items():
        html = html.replace(token, value)

    # 이미지 경로 보정
    html = html.replace('src="../images/', 'src="/images/')
    html = html.replace("src='../images/", "src='/images/")
    html = html.replace('href="../images/', 'href="/images/')
    html = html.replace("href='../images/", "href='/images/")

    # title / description / canonical / og 보강
    html = replace_or_insert_head(html, page)

    # 아직 남은 {{...}} 토큰 제거
    html = re.sub(r"{{[^{}]+}}", "", html)

    return html


def write_report(results: List[Dict[str, str]]) -> None:
    fields = [
        "index",
        "keyword",
        "slug",
        "status",
        "output_path",
        "hash",
        "message",
        "title",
        "description",
        "canonical",
        "generated_at",
    ]

    with open(REPORT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in fields})


def parse_args():
    parser = argparse.ArgumentParser(description="체인지클린 template.html 전용 V6 Pro 생성 엔진")
    parser.add_argument("--input", default="", help="입력 파일. 기본 keywords.xlsx")
    parser.add_argument("--limit", type=int, default=0, help="앞에서 N개만 생성")
    parser.add_argument("--force", action="store_true", help="캐시 무시하고 전체 재생성")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()

    log("make_sites_v6_pro.py 시작")

    pages = read_keywords(args.input)

    if args.limit:
        pages = pages[:args.limit]

    if not pages:
        print("생성할 페이지가 없습니다.")
        return 1

    template = load_template()
    cache = load_cache()
    results: List[Dict[str, str]] = []

    for page in pages:
        out_dir = OUTPUT_DIR / page.slug
        out_file = out_dir / "index.html"

        try:
            html = render_page(page, pages, template)
            page_hash = md5_text(html)

            if not args.force and cache.get(page.slug) == page_hash and out_file.exists():
                status = "SKIP"
                message = "변경 없음"
            else:
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file.write_text(html, encoding="utf-8")
                cache[page.slug] = page_hash
                status = "UPDATED"
                message = "생성 완료"

            results.append({
                "index": str(page.index),
                "keyword": page.keyword,
                "slug": page.slug,
                "status": status,
                "output_path": str(out_file),
                "hash": page_hash,
                "message": message,
                "title": page.title,
                "description": page.description,
                "canonical": page.canonical,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

        except Exception as e:
            results.append({
                "index": str(page.index),
                "keyword": page.keyword,
                "slug": page.slug,
                "status": "ERROR",
                "output_path": str(out_file),
                "hash": "",
                "message": str(e),
                "title": page.title,
                "description": page.description,
                "canonical": page.canonical,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    save_cache(cache)
    write_report(results)

    updated = sum(1 for r in results if r["status"] == "UPDATED")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print(f"완료: 전체 {len(results)} / UPDATED {updated} / SKIP {skipped} / ERROR {errors}")
    print(f"리포트: {REPORT_FILE}")

    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
