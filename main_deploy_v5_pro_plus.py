# -*- coding: utf-8 -*-
"""
V5-5 Pro Plus v2 : main_deploy_v5_pro_plus.py

메인과 지역 SEO 페이지를 분리한 최종 구조용 배포 엔진.

사용 구조
- home_template.html  : 베이스 사이트 메인 홈페이지용
- template.html       : 지역 SEO 랜딩 페이지용. 기존 index.html을 template.html로 이름 변경해서 사용
- deploys/index.html  : 네이버에 등록할 베이스 사이트 결과물

실행 순서
1) 기존 index.html 파일명을 template.html 로 변경
2) home_template.html 을 같은 폴더에 넣기
3) python make_sites_v5.py
4) python main_deploy_v5_pro_plus.py --no-git
5) 확인 후 python main_deploy_v5_pro_plus.py
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
DEPLOYS_DIR = BASE_DIR / "deploys"

HOME_TEMPLATE_FILE = BASE_DIR / "home_template.html"
REPORT_FILE = BASE_DIR / "report_v5.csv"
BACKUP_DIR = BASE_DIR / "backup_index"

REGION_DIR = DEPLOYS_DIR / "region"
SERVICE_DIR = DEPLOYS_DIR / "service"
REGIONS_INDEX_DIR = DEPLOYS_DIR / "regions"
SERVICES_INDEX_DIR = DEPLOYS_DIR / "services"

SITE_URL = "https://changeclean1.netlify.app"
BRAND_NAME = "체인지클린"
PHONE_TEXT = "빠른상담:1688-6751"
PHONE_NUMBER = "1688-6751"


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


def slugify(text: str) -> str:
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
        "입주청소", "이사청소", "준공청소", "상가청소", "사무실청소",
        "빌라청소", "아파트청소", "오피스텔청소", "거주청소",
        "화장실청소", "주방청소", "유리창청소", "곰팡이청소",
        "부분청소", "특수청소"
    ]
    for service in services:
        if service in keyword:
            return service
    return "전문청소"


def read_report_pages() -> List[Page]:
    pages: List[Page] = []

    if REPORT_FILE.exists():
        with open(REPORT_FILE, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keyword = clean(row.get("keyword"))
                slug = clean(row.get("slug")).strip("/")
                if not keyword or not slug:
                    continue
                pages.append(Page(
                    keyword=keyword,
                    slug=slug,
                    title=clean(row.get("title")) or f"{keyword} | {BRAND_NAME}",
                    description=clean(row.get("description")) or f"{keyword} 전문 청소 서비스 안내",
                    canonical=clean(row.get("canonical")) or f"{SITE_URL.rstrip('/')}/{slug}/",
                    region=infer_region(keyword),
                    service=infer_service(keyword),
                ))

    if pages:
        return pages

    if DEPLOYS_DIR.exists():
        for p in sorted(DEPLOYS_DIR.iterdir()):
            if not p.is_dir():
                continue
            if p.name in ["region", "service", "regions", "services", "category"]:
                continue
            if not (p / "index.html").exists():
                continue
            keyword = p.name.replace("-", " ")
            pages.append(Page(
                keyword=keyword,
                slug=p.name,
                title=f"{keyword} | {BRAND_NAME}",
                description=f"{keyword} 전문 청소 서비스 안내",
                canonical=f"{SITE_URL.rstrip('/')}/{p.name}/",
                region=infer_region(keyword),
                service=infer_service(keyword),
            ))

    return pages


def group_by(pages: List[Page], attr: str) -> Dict[str, List[Page]]:
    data = defaultdict(list)
    for page in pages:
        key = clean(getattr(page, attr)) or "기타"
        data[key].append(page)
    return dict(data)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_home_template() -> str:
    if HOME_TEMPLATE_FILE.exists():
        return HOME_TEMPLATE_FILE.read_text(encoding="utf-8")
    raise FileNotFoundError("home_template.html 파일이 없습니다. 같은 폴더에 넣어주세요.")


def schema_block(pages: List[Page]) -> str:
    local_business = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": BRAND_NAME,
        "url": SITE_URL,
        "telephone": PHONE_NUMBER,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "인천광역시 미추홀구",
            "addressRegion": "인천",
            "addressCountry": "KR"
        },
        "areaServed": sorted(list(group_by(pages, "region").keys()))[:80],
        "sameAs": [
            "https://blog.naver.com/changeclean1",
            "https://changeclean.tistory.com/",
            "https://naver.me/5imyvric"
        ]
    }

    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": BRAND_NAME,
        "url": SITE_URL,
        "description": "입주청소, 이사청소, 상가청소, 사무실청소 전문 서비스"
    }

    return (
        '<script type="application/ld+json">' +
        json.dumps(local_business, ensure_ascii=False, indent=2) +
        '</script>\n<script type="application/ld+json">' +
        json.dumps(website, ensure_ascii=False, indent=2) +
        '</script>'
    )


def faq_html() -> str:
    faqs = [
        ("입주청소와 이사청소는 어떻게 다른가요?", "입주청소는 신축 또는 리모델링 후 분진을 중심으로 확인하고, 이사청소는 이전 거주 흔적과 생활 오염을 중심으로 진행합니다."),
        ("상담할 때 어떤 정보를 알려드리면 좋나요?", "지역, 평수, 구조, 희망 날짜, 현장 사진을 알려주시면 더 빠르게 안내할 수 있습니다."),
        ("서울 경기 인천도 가능한가요?", "서울, 경기, 인천 주요 지역을 기준으로 상담 가능하며 일정과 현장 상황에 따라 안내드립니다."),
        ("견적은 어떻게 확인하나요?", "전화 또는 상담폼으로 문의하시면 공간 크기와 작업 범위를 확인한 뒤 안내드립니다."),
    ]
    return "\n".join(
        f'<div class="faq-item"><h3>Q. {esc(q)}</h3><p>{esc(a)}</p></div>'
        for q, a in faqs
    )


def region_links_html(pages: List[Page]) -> str:
    groups = group_by(pages, "region")
    if not groups:
        return '<a href="/regions/">지역별 청소 보기</a>'
    return "\n".join(
        f'<a href="/region/{esc(slugify(name))}/">{esc(name)} 청소</a>'
        for name in sorted(groups.keys())[:80]
    )


def service_links_html(pages: List[Page]) -> str:
    groups = group_by(pages, "service")
    if not groups:
        return '<a href="/services/">서비스별 청소 보기</a>'
    return "\n".join(
        f'<a href="/service/{esc(slugify(name))}/">{esc(name)}</a>'
        for name in sorted(groups.keys())[:40]
    )


def latest_pages_html(pages: List[Page], limit: int = 24) -> str:
    if not pages:
        return '<div class="card"><h3>청소 페이지 준비중</h3><p>지역별 청소 서비스 페이지를 준비하고 있습니다.</p></div>'
    items = []
    for page in pages[:limit]:
        items.append(f"""
<div class="card">
<h3><a href="/{esc(page.slug)}/">{esc(page.keyword)}</a></h3>
<p>{esc(page.description[:95])}</p>
</div>
""")
    return "\n".join(items)


def build_home_index(pages: List[Page]) -> None:
    DEPLOYS_DIR.mkdir(parents=True, exist_ok=True)

    current_index = DEPLOYS_DIR / "index.html"
    if current_index.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(current_index, BACKUP_DIR / f"index_{stamp}.html")

    template = load_home_template()

    replacements = {
        "{{TITLE}}": f"{BRAND_NAME} | 입주청소 이사청소 전문업체",
        "{{DESCRIPTION}}": "체인지클린은 서울·경기·인천 지역 입주청소, 이사청소, 상가청소, 사무실청소를 전문으로 진행하는 청소 전문업체입니다.",
        "{{CANONICAL}}": SITE_URL.rstrip("/") + "/",
        "{{SCHEMA}}": schema_block(pages),
        "{{REGION_LINKS}}": region_links_html(pages),
        "{{SERVICE_LINKS}}": service_links_html(pages),
        "{{LATEST_PAGES}}": latest_pages_html(pages),
        "{{FAQ}}": faq_html(),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    # 혹시 남은 템플릿 토큰은 제거
    template = re.sub(r"{{[A-Z가-힣0-9_]+}}", "", template)

    write_file(DEPLOYS_DIR / "index.html", template)


def simple_layout(title: str, description: str, body: str, canonical: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{esc(canonical)}">
<style>
body{{font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;margin:0;color:#333;line-height:1.7;background:#fff}}
.wrap{{max-width:1080px;margin:0 auto;padding:34px 20px}}
.hero{{background:#004080;color:#fff;padding:56px 20px;text-align:center}}
.hero h1{{margin:0;font-size:2rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:28px}}
.card{{border:1px solid #e5e7eb;border-radius:14px;padding:18px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.04)}}
a{{color:#007bff;text-decoration:none;font-weight:700}}
.footer{{background:#f8f9fa;border-top:1px solid #eee;margin-top:40px;padding:25px;text-align:center;color:#666}}
</style>
</head>
<body>
<section class="hero"><h1>{esc(title)}</h1><p>{esc(description)}</p></section>
<div class="wrap">{body}</div>
<div class="footer">{BRAND_NAME} · {PHONE_TEXT}</div>
</body>
</html>"""


def card(title: str, url: str, desc: str = "") -> str:
    return f'<div class="card"><h3><a href="{esc(url)}">{esc(title)}</a></h3><p>{esc(desc)}</p></div>'


def build_category_pages(pages: List[Page]) -> None:
    regions = group_by(pages, "region")
    services = group_by(pages, "service")

    region_cards = "\n".join(
        card(f"{name} 청소", f"/region/{slugify(name)}/", f"{name} 지역 청소 서비스 {len(items)}개")
        for name, items in sorted(regions.items())
    )
    write_file(
        REGIONS_INDEX_DIR / "index.html",
        simple_layout(
            f"{BRAND_NAME} 지역별 청소",
            "서울·경기·인천 지역별 청소 서비스 목록입니다.",
            f'<div class="grid">{region_cards}</div>',
            f"{SITE_URL.rstrip('/')}/regions/",
        ),
    )

    service_cards = "\n".join(
        card(name, f"/service/{slugify(name)}/", f"{name} 관련 페이지 {len(items)}개")
        for name, items in sorted(services.items())
    )
    write_file(
        SERVICES_INDEX_DIR / "index.html",
        simple_layout(
            f"{BRAND_NAME} 서비스별 청소",
            "입주청소, 이사청소, 상가청소, 사무실청소 등 서비스별 페이지 목록입니다.",
            f'<div class="grid">{service_cards}</div>',
            f"{SITE_URL.rstrip('/')}/services/",
        ),
    )

    for region, items in regions.items():
        cards = "\n".join(card(page.keyword, f"/{page.slug}/", page.description[:100]) for page in items)
        slug = slugify(region)
        write_file(
            REGION_DIR / slug / "index.html",
            simple_layout(
                f"{region} 청소 서비스 | {BRAND_NAME}",
                f"{region} 지역의 입주청소, 이사청소, 상가청소, 사무실청소 페이지입니다.",
                f'<div class="grid">{cards}</div>',
                f"{SITE_URL.rstrip('/')}/region/{slug}/",
            ),
        )

    for service, items in services.items():
        cards = "\n".join(card(page.keyword, f"/{page.slug}/", page.description[:100]) for page in items)
        slug = slugify(service)
        write_file(
            SERVICE_DIR / slug / "index.html",
            simple_layout(
                f"{service} 전문 안내 | {BRAND_NAME}",
                f"{service} 관련 지역별 청소 서비스 페이지입니다.",
                f'<div class="grid">{cards}</div>',
                f"{SITE_URL.rstrip('/')}/service/{slug}/",
            ),
        )


def collect_urls(pages: List[Page]) -> List[str]:
    urls = [
        f"{SITE_URL.rstrip('/')}/",
        f"{SITE_URL.rstrip('/')}/regions/",
        f"{SITE_URL.rstrip('/')}/services/",
    ]
    for page in pages:
        urls.append(f"{SITE_URL.rstrip('/')}/{page.slug}/")
    for region in group_by(pages, "region").keys():
        urls.append(f"{SITE_URL.rstrip('/')}/region/{slugify(region)}/")
    for service in group_by(pages, "service").keys():
        urls.append(f"{SITE_URL.rstrip('/')}/service/{slugify(service)}/")
    return sorted(set(urls))


def build_sitemap(pages: List[Page]) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    body = "\n".join(
        f"""  <url>
    <loc>{esc(url)}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{'1.0' if url.rstrip('/') == SITE_URL.rstrip('/') else '0.8'}</priority>
  </url>"""
        for url in collect_urls(pages)
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    write_file(DEPLOYS_DIR / "sitemap.xml", xml)


def build_robots() -> None:
    write_file(
        DEPLOYS_DIR / "robots.txt",
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n"
    )


def git_run(command: List[str], dry_run: bool = False) -> Tuple[int, str]:
    if dry_run:
        return 0, "DRY RUN: " + " ".join(command)
    try:
        result = subprocess.run(command, cwd=BASE_DIR, capture_output=True, text=True, shell=False)
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError:
        return 127, "Git이 설치되어 있지 않거나 PATH에 없습니다."


def run_git_deploy(message: str, dry_run: bool = False) -> int:
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", message],
        ["git", "push"],
    ]
    for cmd in commands:
        code, output = git_run(cmd, dry_run=dry_run)
        print("$", " ".join(cmd))
        if output.strip():
            print(output.strip())
        if code != 0 and "nothing to commit" not in output.lower():
            return code
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="V5-5 Pro Plus v2 메인/카테고리/Git 배포 엔진")
    parser.add_argument("--no-git", action="store_true", help="Git 배포 실행 안 함")
    parser.add_argument("--dry-run", action="store_true", help="Git 명령 dry-run")
    parser.add_argument("--message", default="", help="Git commit 메시지")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    DEPLOYS_DIR.mkdir(parents=True, exist_ok=True)

    pages = read_report_pages()
    if not pages:
        print("페이지 정보가 없습니다. 먼저 python make_sites_v5.py 를 실행하세요.")
        return 1

    print(f"home_template.html 기반으로 베이스 사이트를 생성합니다. 페이지 수: {len(pages)}")

    build_home_index(pages)
    build_category_pages(pages)
    build_sitemap(pages)
    build_robots()

    print("완료: deploys/index.html, regions, services, region, service, sitemap.xml, robots.txt 생성")

    if not args.no_git:
        msg = args.message or f"V5 Pro Plus v2 deploy {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return run_git_deploy(msg, dry_run=args.dry_run)

    print("Git 배포는 건너뛰었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
