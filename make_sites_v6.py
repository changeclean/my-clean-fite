# -*- coding: utf-8 -*-
"""
make_sites_v6.py

V6 페이지 생성 엔진
기존 make_sites_v5.py를 대체합니다.

핵심 수정:
- template.html 안의 기존 토큰 자동 치환
- {{지역명}}
- {{오늘날짜}}
- {{피드백}}
- {{FAQ}}
- {{페이지번호}}
- {{TITLE}}
- {{DESCRIPTION}}
- {{H1}}
- {{CANONICAL}}
- {{CONTENT}}
- {{INTERNAL_LINKS}}

실행:
python make_sites_v6.py

테스트:
python make_sites_v6.py --limit 100

전체 강제 재생성:
python make_sites_v6.py --force
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

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

CACHE_FILE = CACHE_DIR / "page_hash_v6.json"
REPORT_FILE = BASE_DIR / "report_v5.csv"

SITE_URL = "https://changeclean1.netlify.app"
BRAND_NAME = "체인지클린"
PHONE_TEXT = "빠른상담:1688-6751"


@dataclass
class Page:
    index: int
    keyword: str
    slug: str
    region: str = ""
    service: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    h1: str = ""
    canonical: str = ""
    content: str = ""


def clean(value) -> str:
    if value is None:
        return ""
    try:
        if pd is not None and pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def esc(value) -> str:
    return (
        clean(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def md5(text: str) -> str:
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
    if clean(region):
        return clean(region)
    words = clean(keyword).split()
    if not words:
        return "해당 지역"
    if len(words) >= 2 and words[0] in ["서울", "경기", "인천"]:
        return f"{words[0]} {words[1]}"
    return words[0]


def infer_service(keyword: str, service: str = "") -> str:
    if clean(service):
        return clean(service)
    services = [
        "입주청소", "이사청소", "준공청소", "상가청소", "사무실청소",
        "빌라청소", "아파트청소", "오피스텔청소", "거주청소",
        "화장실청소", "주방청소", "유리창청소", "곰팡이청소",
        "부분청소", "특수청소"
    ]
    for s in services:
        if s in keyword:
            return s
    return "전문청소"


def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ensure_dirs()
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}_make_sites_v6.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_cache() -> Dict[str, str]:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache: Dict[str, str]):
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

    rows: List[Dict[str, Any]]

    if path.suffix.lower() in [".xlsx", ".xls"]:
        if pd is None:
            raise ImportError("엑셀 읽기에는 pandas/openpyxl이 필요합니다.")
        df = pd.read_excel(path).fillna("")
        rows = df.to_dict(orient="records")
    else:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

    pages: List[Page] = []
    seen = set()

    for i, row in enumerate(rows, start=1):
        keyword = clean(row.get("keyword") or row.get("키워드") or row.get("Keyword"))
        if not keyword:
            continue

        slug = slugify(row.get("slug") or row.get("Slug") or row.get("url_slug") or keyword)
        if not slug:
            continue

        base_slug = slug
        n = 2
        while slug in seen:
            slug = f"{base_slug}-{n}"
            n += 1
        seen.add(slug)

        region = infer_region(keyword, row.get("region") or row.get("지역"))
        service = infer_service(keyword, row.get("service") or row.get("서비스"))

        title = clean(row.get("title") or row.get("Title")) or f"{keyword} | {BRAND_NAME}"
        description = clean(row.get("description") or row.get("Description") or row.get("meta_description"))
        if not description:
            description = f"{keyword} 전문업체 {BRAND_NAME}. 입주청소, 이사청소, 상가청소, 사무실청소를 현장 상황에 맞춰 꼼꼼하게 진행합니다."
        description = description[:155]

        h1 = clean(row.get("h1") or row.get("H1")) or keyword
        canonical = clean(row.get("canonical") or row.get("url")) or f"{SITE_URL.rstrip('/')}/{slug}/"
        content = clean(row.get("content") or row.get("본문"))

        pages.append(Page(
            index=i,
            keyword=keyword,
            slug=slug,
            region=region,
            service=service,
            category=clean(row.get("category") or service),
            title=title,
            description=description,
            h1=h1,
            canonical=canonical,
            content=content,
        ))

    return pages


def default_template() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESCRIPTION}}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{{CANONICAL}}">
</head>
<body>
<h1>{{H1}}</h1>
{{CONTENT}}
{{INTERNAL_LINKS}}
</body>
</html>"""


def load_template() -> str:
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return default_template()


def build_feedback(page: Page) -> str:
    return f"""
{page.keyword} 현장은 공간 구조와 오염 상태에 따라 작업 범위가 달라질 수 있습니다.
{BRAND_NAME}은 주방, 욕실, 창틀, 바닥, 수납장 내부처럼 고객이 실제로 확인하는 구역을 중심으로 꼼꼼하게 점검합니다.
상담 시 평수, 구조, 희망 날짜, 현장 사진을 알려주시면 더 정확한 안내가 가능합니다.
""".strip()


def build_faq(page: Page) -> str:
    faqs = [
        (f"{page.keyword} 작업 시간은 얼마나 걸리나요?", "평수, 구조, 오염도, 작업 범위에 따라 달라집니다. 상담 시 현장 정보를 알려주시면 더 정확하게 안내드립니다."),
        ("청소 범위는 어디까지 포함되나요?", "기본적으로 주방, 욕실, 창틀, 바닥, 수납장 내부 등 생활 공간 중심으로 진행합니다."),
        ("견적 상담은 어떻게 하나요?", "전화 상담 또는 예약폼으로 지역, 평수, 희망 날짜를 남겨주시면 확인 후 안내드립니다."),
        ("당일 예약도 가능한가요?", "일정에 여유가 있는 경우 가능하지만, 원하는 날짜가 있다면 미리 상담하는 것이 좋습니다."),
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


def build_content(page: Page) -> str:
    if page.content:
        return page.content

    return f"""
<section>
<h2>{esc(page.keyword)} 서비스 안내</h2>
<p>{esc(page.keyword)}는 단순히 보이는 먼지만 닦는 작업이 아니라, 공간 구조와 오염 상태를 함께 확인해야 하는 청소입니다. 특히 {esc(page.region)} 현장은 주거 형태와 마감재 상태가 다르기 때문에 현장에 맞춘 작업 순서가 중요합니다.</p>
<p>{BRAND_NAME}은 주방, 욕실, 창틀, 바닥, 수납장 내부 등 고객이 실제로 확인하는 구역을 중심으로 꼼꼼하게 점검합니다.</p>
</section>

<section>
<h2>{esc(page.service)} 작업 범위</h2>
<p>기본 작업은 주방, 욕실, 창틀, 바닥, 문틀, 수납장 내부를 중심으로 진행됩니다. 오염도가 높은 부분은 현장 확인 후 반복 작업이 필요할 수 있습니다.</p>
<p>상담 시 평수, 구조, 희망 날짜, 현장 사진을 알려주시면 더 정확한 안내가 가능합니다.</p>
</section>

<section>
<h2>{BRAND_NAME} 상담 안내</h2>
<p>{esc(page.keyword)}가 필요하시다면 전화 또는 예약폼을 통해 문의해 주세요. 현장 상황에 맞춰 작업 범위와 일정을 안내드립니다.</p>
<p><strong>{PHONE_TEXT}</strong></p>
</section>
"""


def build_internal_links(page: Page, pages: List[Page], limit: int = 30) -> str:
    links = []
    for other in pages:
        if other.slug == page.slug:
            continue
        same_region = other.region == page.region
        same_service = other.service == page.service
        if same_region or same_service:
            links.append(f'<a href="/{esc(other.slug)}/">{esc(other.keyword)}</a>')
        if len(links) >= limit:
            break

    if not links:
        for other in pages:
            if other.slug == page.slug:
                continue
            links.append(f'<a href="/{esc(other.slug)}/">{esc(other.keyword)}</a>')
            if len(links) >= limit:
                break

    return "\n".join(links)


def build_schema(page: Page) -> str:
    obj = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": BRAND_NAME,
        "url": page.canonical,
        "description": page.description,
        "telephone": "1688-6751",
        "areaServed": page.region,
    }
    return json.dumps(obj, ensure_ascii=False, indent=2)


def inject_missing_head_seo(html: str, page: Page) -> str:
    # 기존 템플릿에 title/description/canonical이 없거나 {{지역명}} 기반인 경우 보강
    if "<head" not in html.lower():
        return html

    # 남은 title이 비었거나 토큰 제거 후 약하면 title 교체
    html = re.sub(r"<title>.*?</title>", f"<title>{esc(page.title)}</title>", html, flags=re.I | re.S)

    if 'name="description"' not in html.lower() and "name='description'" not in html.lower():
        html = re.sub(r"</head>", f'<meta name="description" content="{esc(page.description)}">\n</head>', html, flags=re.I)

    if 'rel="canonical"' not in html.lower() and "rel='canonical'" not in html.lower():
        html = re.sub(r"</head>", f'<link rel="canonical" href="{esc(page.canonical)}">\n</head>', html, flags=re.I)

    if "application/ld+json" not in html:
        html = re.sub(r"</head>", f'<script type="application/ld+json">\n{build_schema(page)}\n</script>\n</head>', html, flags=re.I)

    return html


def render_page(page: Page, pages: List[Page], template: str) -> str:
    context = {
        "{{지역명}}": page.keyword,
        "{{오늘날짜}}": datetime.now().strftime("%Y.%m.%d"),
        "{{피드백}}": build_feedback(page),
        "{{FAQ}}": build_faq(page),
        "{{페이지번호}}": build_internal_links(page, pages),
        "{{TITLE}}": page.title,
        "{{DESCRIPTION}}": page.description,
        "{{H1}}": page.h1,
        "{{CANONICAL}}": page.canonical,
        "{{CONTENT}}": build_content(page),
        "{{INTERNAL_LINKS}}": build_internal_links(page, pages),
        "{{KEYWORD}}": page.keyword,
        "{{REGION}}": page.region,
        "{{SERVICE}}": page.service,
        "{{CATEGORY}}": page.category,
        "{{BRAND_NAME}}": BRAND_NAME,
        "{{PHONE_TEXT}}": PHONE_TEXT,
        "{{SCHEMA}}": build_schema(page),
    }

    html = template
    for key, value in context.items():
        html = html.replace(key, value)

    # 이미지 경로 보정
    html = html.replace('src="../images/', 'src="/images/')
    html = html.replace("src='../images/", "src='/images/")

    # 남은 템플릿 토큰 제거
    html = re.sub(r"{{[^{}]+}}", "", html)

    html = inject_missing_head_seo(html, page)
    return html


def write_report(results: List[Dict[str, str]]):
    fields = ["index", "keyword", "slug", "status", "output_path", "hash", "message", "title", "description", "canonical", "generated_at"]
    with open(REPORT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fields})


def parse_args():
    parser = argparse.ArgumentParser(description="V6 페이지 생성 엔진")
    parser.add_argument("--input", default="", help="입력 파일. 기본 keywords.xlsx")
    parser.add_argument("--limit", type=int, default=0, help="테스트용 개수 제한")
    parser.add_argument("--force", action="store_true", help="전체 강제 재생성")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()

    log("make_sites_v6.py 시작")

    pages = read_keywords(args.input)
    if args.limit:
        pages = pages[:args.limit]

    if not pages:
        print("생성할 페이지가 없습니다.")
        return 1

    template = load_template()
    cache = load_cache()
    results = []

    for page in pages:
        try:
            html = render_page(page, pages, template)
            h = md5(html)
            out_dir = OUTPUT_DIR / page.slug
            out_file = out_dir / "index.html"

            if not args.force and cache.get(page.slug) == h and out_file.exists():
                status = "SKIP"
                message = "변경 없음"
            else:
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file.write_text(html, encoding="utf-8")
                cache[page.slug] = h
                status = "UPDATED"
                message = "생성 완료"

            results.append({
                "index": str(page.index),
                "keyword": page.keyword,
                "slug": page.slug,
                "status": status,
                "output_path": str(out_file),
                "hash": h,
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
                "output_path": "",
                "hash": "",
                "message": str(e),
                "title": "",
                "description": "",
                "canonical": "",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    save_cache(cache)
    write_report(results)

    updated = sum(1 for r in results if r["status"] == "UPDATED")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print(f"완료: 전체 {len(results)} / UPDATED {updated} / SKIP {skipped} / ERROR {errors}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
