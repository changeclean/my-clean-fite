# -*- coding: utf-8 -*-
"""
V5-5 Pro : main_deploy_v5_pro.py

메인 홈페이지 + 지역 카테고리 + 서비스 카테고리 + sitemap + robots + Git 자동 배포

역할
- deploys/index.html 메인 허브 페이지 생성
- deploys/regions/index.html 지역 전체 카테고리 생성
- deploys/services/index.html 서비스 전체 카테고리 생성
- deploys/region/{지역}/index.html 지역별 허브 페이지 생성
- deploys/service/{서비스}/index.html 서비스별 허브 페이지 생성
- sitemap.xml 생성
- robots.txt 생성
- Git add / commit / push 자동 실행

실행:
    python main_deploy_v5_pro.py

주의:
    먼저 python make_sites_v5.py 로 개별 페이지를 생성한 뒤 실행하세요.
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent
DEPLOYS_DIR = BASE_DIR / "deploys"
REPORT_FILE = BASE_DIR / "report_v5.csv"

SITE_URL = "https://changeclean1.netlify.app"
BRAND_NAME = "체인지클린"
PHONE_TEXT = "빠른상담:1688-6751"

REGION_DIR = DEPLOYS_DIR / "region"
SERVICE_DIR = DEPLOYS_DIR / "service"
REGIONS_INDEX_DIR = DEPLOYS_DIR / "regions"
SERVICES_INDEX_DIR = DEPLOYS_DIR / "services"

SITEMAP_FILE = DEPLOYS_DIR / "sitemap.xml"
ROBOTS_FILE = DEPLOYS_DIR / "robots.txt"


@dataclass
class Page:
    keyword: str
    slug: str
    title: str
    description: str
    canonical: str
    region: str = ""
    service: str = ""


def clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def esc(value) -> str:
    return html.escape(clean(value), quote=True)


def slugify_korean(text: str) -> str:
    text = clean(text).lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9가-힣_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-") or "category"


def infer_region(keyword: str) -> str:
    words = clean(keyword).split()
    if not words:
        return "기타"
    if len(words) >= 2 and words[0] in ["서울", "경기", "인천"]:
        return f"{words[0]} {words[1]}"
    return words[0]


def infer_service(keyword: str) -> str:
    services = [
        "입주청소",
        "이사청소",
        "준공청소",
        "상가청소",
        "사무실청소",
        "빌라청소",
        "아파트청소",
        "오피스텔청소",
        "거주청소",
        "화장실청소",
        "주방청소",
        "유리창청소",
        "곰팡이청소",
    ]
    for s in services:
        if s in keyword:
            return s
    return "전문청소"


def read_report_pages() -> List[Page]:
    pages: List[Page] = []

    if REPORT_FILE.exists():
        with open(REPORT_FILE, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keyword = clean(row.get("keyword"))
                slug = clean(row.get("slug"))
                if not keyword or not slug:
                    continue
                pages.append(Page(
                    keyword=keyword,
                    slug=slug.strip("/"),
                    title=clean(row.get("title")) or keyword,
                    description=clean(row.get("description")) or f"{keyword} 전문 청소 서비스",
                    canonical=clean(row.get("canonical")) or f"{SITE_URL.rstrip('/')}/{slug.strip('/')}/",
                    region=infer_region(keyword),
                    service=infer_service(keyword),
                ))

    if pages:
        return pages

    # report_v5.csv가 없을 경우 deploys 폴더 기반으로 최소 구성
    for p in sorted(DEPLOYS_DIR.iterdir()) if DEPLOYS_DIR.exists() else []:
        if not p.is_dir():
            continue
        if p.name in ["region", "service", "regions", "services", "category"]:
            continue
        index_file = p / "index.html"
        if not index_file.exists():
            continue
        keyword = p.name.replace("-", " ")
        pages.append(Page(
            keyword=keyword,
            slug=p.name,
            title=keyword,
            description=f"{keyword} 전문 청소 서비스",
            canonical=f"{SITE_URL.rstrip('/')}/{p.name}/",
            region=infer_region(keyword),
            service=infer_service(keyword),
        ))

    return pages


def html_layout(title: str, description: str, body: str, canonical: str = "") -> str:
    canonical_tag = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": BRAND_NAME,
        "url": SITE_URL,
        "telephone": PHONE_TEXT.replace("빠른상담:", ""),
    }
    schema_text = str(schema).replace("'", '"')

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{canonical_tag}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(canonical or SITE_URL)}">
<script type="application/ld+json">{schema_text}</script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:Arial,'Noto Sans KR',sans-serif;color:#172033;background:#ffffff;line-height:1.7}}
a{{color:#0369a1;text-decoration:none}}
a:hover{{text-decoration:underline}}
.header{{background:linear-gradient(135deg,#e0f2fe,#ffffff);border-bottom:1px solid #e5e7eb}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 20px}}
.hero{{padding:58px 20px}}
.hero h1{{font-size:40px;line-height:1.25;margin:0 0 16px;color:#0f172a}}
.hero p{{font-size:19px;color:#334155;max-width:780px}}
.nav{{padding:16px 0;border-top:1px solid #e5e7eb}}
.nav a{{display:inline-block;margin:6px 16px 6px 0;font-weight:700}}
main{{padding:40px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}
.card{{padding:20px;border:1px solid #e5e7eb;border-radius:16px;background:#fff;box-shadow:0 3px 12px rgba(15,23,42,.04)}}
.card h3{{margin:0 0 8px;font-size:20px}}
.section{{margin:46px 0}}
.section h2{{font-size:28px;margin:0 0 18px}}
.list a{{display:block;padding:12px 0;border-bottom:1px solid #edf2f7}}
.cta{{margin:44px 0;padding:28px;border-radius:18px;background:#eff6ff;border:1px solid #bfdbfe}}
.footer{{margin-top:40px;padding:30px 0;text-align:center;background:#111827;color:#fff}}
.badge{{display:inline-block;padding:5px 10px;border-radius:999px;background:#dbeafe;color:#1e40af;font-size:13px;font-weight:700}}
</style>
</head>
<body>
<header class="header">
<div class="wrap hero">
<span class="badge">{BRAND_NAME}</span>
<h1>{esc(title)}</h1>
<p>{esc(description)}</p>
</div>
<div class="wrap nav">
<a href="/">홈</a>
<a href="/regions/">지역별 청소</a>
<a href="/services/">서비스별 청소</a>
<a href="/sitemap.xml">사이트맵</a>
</div>
</header>
<main class="wrap">
{body}
</main>
<footer class="footer">
<div class="wrap">© {datetime.now().year} {BRAND_NAME} · {PHONE_TEXT}</div>
</footer>
</body>
</html>"""


def page_card(page: Page) -> str:
    return f"""
<div class="card">
<h3><a href="/{esc(page.slug)}/">{esc(page.keyword)}</a></h3>
<p>{esc(page.description[:90])}</p>
</div>
"""


def category_card(name: str, url: str, count: int, desc: str) -> str:
    return f"""
<div class="card">
<h3><a href="{esc(url)}">{esc(name)}</a></h3>
<p>{esc(desc)}</p>
<p><strong>{count}</strong>개 페이지</p>
</div>
"""


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_home(pages: List[Page]):
    regions = group_by(pages, "region")
    services = group_by(pages, "service")
    latest = pages[:24]

    region_cards = "\n".join(
        category_card(k, f"/region/{slugify_korean(k)}/", len(v), f"{k} 지역 청소 서비스 모음")
        for k, v in sorted(regions.items())[:18]
    )
    service_cards = "\n".join(
        category_card(k, f"/service/{slugify_korean(k)}/", len(v), f"{k} 전문 서비스 안내")
        for k, v in sorted(services.items())[:12]
    )
    latest_cards = "\n".join(page_card(p) for p in latest)

    body = f"""
<section class="section">
<h2>지역별 청소 서비스</h2>
<div class="grid">{region_cards}</div>
</section>

<section class="section">
<h2>서비스별 청소 안내</h2>
<div class="grid">{service_cards}</div>
</section>

<section class="section">
<h2>최근 생성된 청소 페이지</h2>
<div class="grid">{latest_cards}</div>
</section>

<section class="cta">
<h2>청소 상담이 필요하신가요?</h2>
<p>입주청소, 이사청소, 상가청소, 사무실청소 등 현장 상황에 맞춰 상담해드립니다.</p>
<p><strong>{PHONE_TEXT}</strong></p>
</section>
"""
    html_doc = html_layout(
        title=f"{BRAND_NAME} 지역별 청소 전문 서비스",
        description="서울, 경기, 인천 지역의 입주청소, 이사청소, 상가청소, 사무실청소 정보를 한눈에 확인할 수 있는 청소 서비스 허브입니다.",
        body=body,
        canonical=SITE_URL,
    )
    write_file(DEPLOYS_DIR / "index.html", html_doc)


def group_by(pages: List[Page], attr: str) -> Dict[str, List[Page]]:
    d = defaultdict(list)
    for p in pages:
        key = clean(getattr(p, attr)) or "기타"
        d[key].append(p)
    return dict(d)


def build_regions_index(pages: List[Page]):
    groups = group_by(pages, "region")
    cards = "\n".join(
        category_card(name, f"/region/{slugify_korean(name)}/", len(items), f"{name} 청소 페이지 전체 보기")
        for name, items in sorted(groups.items())
    )
    body = f"""
<section class="section">
<h2>지역별 카테고리</h2>
<div class="grid">{cards}</div>
</section>
"""
    write_file(
        REGIONS_INDEX_DIR / "index.html",
        html_layout(
            title=f"{BRAND_NAME} 지역별 청소 카테고리",
            description="서울, 경기, 인천 및 주요 지역별 청소 서비스 페이지를 모았습니다.",
            body=body,
            canonical=f"{SITE_URL.rstrip()}/regions/",
        ),
    )


def build_services_index(pages: List[Page]):
    groups = group_by(pages, "service")
    cards = "\n".join(
        category_card(name, f"/service/{slugify_korean(name)}/", len(items), f"{name} 관련 페이지 전체 보기")
        for name, items in sorted(groups.items())
    )
    body = f"""
<section class="section">
<h2>서비스별 카테고리</h2>
<div class="grid">{cards}</div>
</section>
"""
    write_file(
        SERVICES_INDEX_DIR / "index.html",
        html_layout(
            title=f"{BRAND_NAME} 서비스별 청소 카테고리",
            description="입주청소, 이사청소, 상가청소, 사무실청소 등 서비스별 청소 정보를 모았습니다.",
            body=body,
            canonical=f"{SITE_URL.rstrip()}/services/",
        ),
    )


def build_region_pages(pages: List[Page]):
    groups = group_by(pages, "region")
    for region, items in groups.items():
        cards = "\n".join(page_card(p) for p in items)
        body = f"""
<section class="section">
<h2>{esc(region)} 청소 서비스 목록</h2>
<p>{esc(region)} 지역의 입주청소, 이사청소, 상가청소, 사무실청소 관련 페이지를 확인할 수 있습니다.</p>
<div class="grid">{cards}</div>
</section>
"""
        slug = slugify_korean(region)
        write_file(
            REGION_DIR / slug / "index.html",
            html_layout(
                title=f"{region} 청소 서비스 | {BRAND_NAME}",
                description=f"{region} 지역 청소 서비스 안내. 입주청소, 이사청소, 상가청소, 사무실청소 정보를 확인하세요.",
                body=body,
                canonical=f"{SITE_URL.rstrip()}/region/{slug}/",
            ),
        )


def build_service_pages(pages: List[Page]):
    groups = group_by(pages, "service")
    for service, items in groups.items():
        cards = "\n".join(page_card(p) for p in items)
        body = f"""
<section class="section">
<h2>{esc(service)} 페이지 목록</h2>
<p>{esc(service)} 관련 지역별 페이지를 한곳에서 확인할 수 있습니다.</p>
<div class="grid">{cards}</div>
</section>
"""
        slug = slugify_korean(service)
        write_file(
            SERVICE_DIR / slug / "index.html",
            html_layout(
                title=f"{service} 전문 안내 | {BRAND_NAME}",
                description=f"{service} 관련 지역별 청소 정보를 모았습니다. 현장 상황에 맞는 청소 상담을 받아보세요.",
                body=body,
                canonical=f"{SITE_URL.rstrip()}/service/{slug}/",
            ),
        )


def collect_all_urls(pages: List[Page]) -> List[str]:
    urls = [
        f"{SITE_URL.rstrip()}/",
        f"{SITE_URL.rstrip()}/regions/",
        f"{SITE_URL.rstrip()}/services/",
    ]

    for p in pages:
        urls.append(f"{SITE_URL.rstrip()}/{p.slug.strip('/')}/")

    for region in group_by(pages, "region").keys():
        urls.append(f"{SITE_URL.rstrip()}/region/{slugify_korean(region)}/")

    for service in group_by(pages, "service").keys():
        urls.append(f"{SITE_URL.rstrip()}/service/{slugify_korean(service)}/")

    return sorted(set(urls))


def build_sitemap(pages: List[Page]):
    today = datetime.now().strftime("%Y-%m-%d")
    urls = collect_all_urls(pages)
    body = "\n".join(
        f"""  <url>
    <loc>{esc(url)}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{'1.0' if url.rstrip('/') == SITE_URL.rstrip('/') else '0.8'}</priority>
  </url>"""
        for url in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    write_file(SITEMAP_FILE, xml)


def build_robots():
    text = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL.rstrip()}/sitemap.xml
"""
    write_file(ROBOTS_FILE, text)


def git_run(command: List[str], dry_run: bool = False) -> Tuple[int, str]:
    if dry_run:
        return 0, "DRY RUN: " + " ".join(command)
    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            shell=False,
        )
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError:
        return 127, "Git이 설치되어 있지 않거나 PATH에 없습니다."


def run_git_deploy(message: str, dry_run: bool = False):
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", message],
        ["git", "push"],
    ]

    for cmd in commands:
        code, output = git_run(cmd, dry_run=dry_run)
        print("$", " ".join(cmd))
        print(output.strip())

        # commit할 변경사항이 없는 경우는 치명적 오류로 보지 않음
        if code != 0 and "nothing to commit" not in output.lower():
            print("Git 명령 오류가 발생했습니다.")
            return code

    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="V5-5 Pro 메인/카테고리/Git 배포 엔진")
    parser.add_argument("--no-git", action="store_true", help="Git 배포 실행 안 함")
    parser.add_argument("--dry-run", action="store_true", help="Git 명령만 dry-run")
    parser.add_argument("--message", default="", help="Git commit 메시지")
    return parser.parse_args()


def main():
    args = parse_args()

    DEPLOYS_DIR.mkdir(parents=True, exist_ok=True)

    pages = read_report_pages()
    if not pages:
        print("페이지 정보가 없습니다. 먼저 python make_sites_v5.py 를 실행하세요.")
        return 1

    print(f"페이지 {len(pages)}개 기준으로 Pro 허브를 생성합니다.")

    build_home(pages)
    build_regions_index(pages)
    build_services_index(pages)
    build_region_pages(pages)
    build_service_pages(pages)
    build_sitemap(pages)
    build_robots()

    print("메인/지역/서비스/사이트맵/robots 생성 완료")

    if not args.no_git:
        msg = args.message or f"V5 Pro deploy {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return run_git_deploy(msg, dry_run=args.dry_run)

    print("Git 배포는 건너뛰었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
