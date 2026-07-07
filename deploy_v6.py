# -*- coding: utf-8 -*-
"""
deploy_v6.py
V6 Fixed - 체인지클린 SEO 원클릭 배포 엔진

사용:
python deploy_v6.py --skip-keywords --no-git
python deploy_v6.py --skip-keywords

기능:
- report_v5.csv 컬럼 자동 인식
- report_v5.csv 인식 실패 시 deploys 폴더 직접 스캔
- sitemap.xml 정상 XML sitemapindex 생성
- 50,000 URL 단위 sitemap 자동 분할
- rss.xml 생성
- robots.txt 생성
- Git push 선택 실행
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
BACKUP_DIR = BASE_DIR / "backup_v6"

SITE_URL = "https://changeclean1.netlify.app"
BRAND_NAME = "체인지클린"
PHONE_TEXT = "빠른상담:1688-6751"
PHONE_NUMBER = "1688-6751"

HOME_TEMPLATE_FILE = BASE_DIR / "home_template.html"
PAGE_TEMPLATE_FILE = BASE_DIR / "template.html"
OLD_INDEX_FILE = BASE_DIR / "index.html"
REPORT_FILE = BASE_DIR / "report_v5.csv"

MAX_URLS_PER_SITEMAP = 50000


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
    return "" if value is None else str(value).strip()


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
        "부분청소", "특수청소", "전문청소"
    ]
    for s in services:
        if s in keyword:
            return s
    return "전문청소"


def pick(row: Dict[str, str], names: List[str]) -> str:
    for name in names:
        if name in row and clean(row.get(name)):
            return clean(row.get(name))
    norm = {str(k).strip().lower(): k for k in row.keys()}
    for name in names:
        key = name.strip().lower()
        if key in norm and clean(row.get(norm[key])):
            return clean(row.get(norm[key]))
    return ""


def slug_from_output_path(path_text: str) -> str:
    path_text = clean(path_text).replace("\\", "/")
    if not path_text:
        return ""
    parts = [p for p in path_text.split("/") if p]
    if "deploys" in parts:
        idx = parts.index("deploys")
        if len(parts) > idx + 1:
            return parts[idx + 1].strip("/")
    if len(parts) >= 2 and parts[-1].lower() == "index.html":
        return parts[-2].strip("/")
    return ""


def keyword_from_slug(slug: str) -> str:
    return clean(slug).replace("-", " ")


def read_report_pages() -> List[Page]:
    if not REPORT_FILE.exists():
        return []

    pages: List[Page] = []
    with open(REPORT_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []

    if not rows:
        return []

    print("report_v5.csv 컬럼:", ", ".join(fields))

    for row in rows:
        status = pick(row, ["status", "Status", "STATUS"])
        if status.upper() == "ERROR":
            continue

        keyword = pick(row, ["keyword", "키워드", "Keyword", "KEYWORD", "query", "name"])
        slug = pick(row, ["slug", "Slug", "SLUG", "url_slug"])
        output_path = pick(row, ["output_path", "file", "filename", "저장경로"])
        title = pick(row, ["title", "Title", "TITLE", "seo_title"])
        description = pick(row, ["description", "Description", "DESCRIPTION", "meta_description", "desc"])
        canonical = pick(row, ["canonical", "Canonical", "CANONICAL", "url"])

        if not slug:
            slug = slug_from_output_path(output_path)
        slug = clean(slug).strip("/")

        if not keyword:
            keyword = title or keyword_from_slug(slug)
        if not slug:
            continue

        if not title:
            title = f"{keyword} | {BRAND_NAME}"
        if not description:
            description = f"{keyword} 전문 청소 서비스 안내"
        if not canonical:
            canonical = f"{SITE_URL.rstrip('/')}/{slug}/"

        pages.append(Page(
            keyword=keyword,
            slug=slug,
            title=title,
            description=description,
            canonical=canonical,
            region=infer_region(keyword),
            service=infer_service(keyword),
        ))

    unique = {}
    for p in pages:
        unique.setdefault(p.slug, p)

    return list(unique.values())


def scan_deploys_pages() -> List[Page]:
    pages: List[Page] = []
    if not DEPLOYS_DIR.exists():
        return pages

    skip = {"region", "service", "regions", "services", "category", "images", "assets", "css", "js"}

    for p in sorted(DEPLOYS_DIR.iterdir()):
        if not p.is_dir() or p.name in skip:
            continue
        if not (p / "index.html").exists():
            continue

        keyword = keyword_from_slug(p.name)
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


def get_pages() -> List[Page]:
    pages = read_report_pages()
    if pages:
        print(f"report_v5.csv에서 페이지 {len(pages)}개 인식")
        return pages

    pages = scan_deploys_pages()
    if pages:
        print(f"deploys 폴더에서 페이지 {len(pages)}개 인식")
        return pages

    return []


def group_by(pages: List[Page], attr: str) -> Dict[str, List[Page]]:
    data = defaultdict(list)
    for p in pages:
        key = clean(getattr(p, attr)) or "기타"
        data[key].append(p)
    return dict(data)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def default_home_template() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESCRIPTION}}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{{CANONICAL}}">
{{SCHEMA}}
<style>
body{margin:0;font-family:'Apple SD Gothic Neo','Malgun Gothic',Arial,sans-serif;color:#243044;line-height:1.7}
a{text-decoration:none;color:#006fd6}
.wrap{max-width:1160px;margin:0 auto;padding:0 20px}
.hero{background:linear-gradient(135deg,#003b78,#006fd6);color:white;padding:76px 20px;text-align:center}
.hero h1{font-size:2.4rem;margin:0 0 18px}
.btn{display:inline-block;background:#ffcc00;color:#111!important;padding:14px 26px;border-radius:999px;font-weight:800;margin:6px}
.section{padding:48px 0}.blue{background:#f2f8ff}.section h2{text-align:center;color:#003b78}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}
.card{border:1px solid #e6edf5;border-radius:18px;padding:22px;background:#fff}
.links a{display:inline-block;padding:9px 13px;margin:5px;border-radius:999px;background:white;border:1px solid #d7e8ff;font-weight:700}
.faq-item{border-bottom:1px solid #e5e7eb;padding:17px 0}
.footer{background:#111827;color:white;padding:32px 20px;text-align:center}
.floating-tel{position:fixed;right:24px;bottom:24px;background:#ffcc00;color:#111!important;padding:14px 22px;border-radius:999px;font-weight:900;z-index:999}
</style>
</head>
<body>
<section class="hero"><div class="wrap">
<h1>체인지클린 입주청소 · 이사청소 전문업체</h1>
<p>서울·경기·인천 주요 지역의 청소를 현장 상황에 맞춰 꼼꼼하게 진행합니다.</p>
<p><a class="btn" href="tel:16886751">📞 1688-6751 바로상담</a></p>
</div></section>
<section class="section blue"><div class="wrap"><h2>지역별 바로가기</h2><div class="links">{{REGION_LINKS}}</div></div></section>
<section class="section"><div class="wrap"><h2>서비스별 바로가기</h2><div class="links">{{SERVICE_LINKS}}</div></div></section>
<section class="section blue"><div class="wrap"><h2>최근 청소 페이지</h2><div class="grid">{{LATEST_PAGES}}</div></div></section>
<section class="section"><div class="wrap"><h2>자주 묻는 질문</h2>{{FAQ}}</div></section>
<footer class="footer"><strong>체인지클린</strong><br>대표번호 1688-6751<br><a href="/sitemap.xml" style="color:#fff">사이트맵</a></footer>
<a href="tel:16886751" class="floating-tel">📞 견적문의</a>
</body></html>"""


def ensure_templates() -> None:
    DEPLOYS_DIR.mkdir(parents=True, exist_ok=True)

    if not HOME_TEMPLATE_FILE.exists():
        print("home_template.html이 없어 기본 메인 템플릿을 생성합니다.")
        HOME_TEMPLATE_FILE.write_text(default_home_template(), encoding="utf-8")

    if not PAGE_TEMPLATE_FILE.exists() and OLD_INDEX_FILE.exists():
        print("template.html이 없어 index.html을 template.html로 복사합니다.")
        shutil.copy2(OLD_INDEX_FILE, PAGE_TEMPLATE_FILE)


def schema_block(pages: List[Page]) -> str:
    obj = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": BRAND_NAME,
        "url": SITE_URL,
        "telephone": PHONE_NUMBER,
        "areaServed": sorted(list(group_by(pages, "region").keys()))[:80],
    }
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, indent=2) + '</script>'


def faq_html() -> str:
    faqs = [
        ("입주청소와 이사청소는 어떻게 다른가요?", "입주청소는 신축 분진 중심, 이사청소는 생활 오염 중심으로 진행합니다."),
        ("상담할 때 어떤 정보를 알려드리면 좋나요?", "지역, 평수, 구조, 희망 날짜, 현장 사진을 알려주시면 빠릅니다."),
        ("서울 경기 인천도 가능한가요?", "서울, 경기, 인천 주요 지역을 기준으로 상담 가능합니다."),
    ]
    return "\n".join(f'<div class="faq-item"><h3>Q. {esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in faqs)


def region_links_html(pages: List[Page]) -> str:
    return "\n".join(
        f'<a href="/region/{esc(slugify(name))}/">{esc(name)} 청소</a>'
        for name in sorted(group_by(pages, "region").keys())[:100]
    )


def service_links_html(pages: List[Page]) -> str:
    return "\n".join(
        f'<a href="/service/{esc(slugify(name))}/">{esc(name)}</a>'
        for name in sorted(group_by(pages, "service").keys())[:60]
    )


def latest_pages_html(pages: List[Page], limit: int = 24) -> str:
    return "\n".join(
        f'<div class="card"><h3><a href="/{esc(p.slug)}/">{esc(p.keyword)}</a></h3><p>{esc(p.description[:95])}</p></div>'
        for p in pages[:limit]
    )


def build_home_index(pages: List[Page]) -> None:
    current = DEPLOYS_DIR / "index.html"
    if current.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current, BACKUP_DIR / f"index_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

    template = HOME_TEMPLATE_FILE.read_text(encoding="utf-8")
    replacements = {
        "{{TITLE}}": f"{BRAND_NAME} | 입주청소 이사청소 전문업체",
        "{{DESCRIPTION}}": "체인지클린은 서울·경기·인천 지역 입주청소, 이사청소, 상가청소, 사무실청소 전문업체입니다.",
        "{{CANONICAL}}": SITE_URL.rstrip("/") + "/",
        "{{SCHEMA}}": schema_block(pages),
        "{{REGION_LINKS}}": region_links_html(pages),
        "{{SERVICE_LINKS}}": service_links_html(pages),
        "{{LATEST_PAGES}}": latest_pages_html(pages),
        "{{FAQ}}": faq_html(),
    }

    for k, v in replacements.items():
        template = template.replace(k, v)

    template = re.sub(r"{{[A-Z가-힣0-9_]+}}", "", template)
    write_file(DEPLOYS_DIR / "index.html", template)


def simple_layout(title: str, description: str, body: str, canonical: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{esc(canonical)}">
<style>body{{font-family:'Malgun Gothic',sans-serif;line-height:1.7;margin:0}}.hero{{background:#004080;color:white;padding:45px 20px;text-align:center}}.wrap{{max-width:1080px;margin:0 auto;padding:30px 20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}.card{{border:1px solid #ddd;border-radius:12px;padding:16px}}a{{color:#007bff;text-decoration:none;font-weight:700}}</style>
</head><body><section class="hero"><h1>{esc(title)}</h1><p>{esc(description)}</p></section><div class="wrap">{body}</div></body></html>"""


def card(title: str, url: str, desc: str) -> str:
    return f'<div class="card"><h3><a href="{esc(url)}">{esc(title)}</a></h3><p>{esc(desc)}</p></div>'


def build_category_pages(pages: List[Page]) -> None:
    regions = group_by(pages, "region")
    services = group_by(pages, "service")

    region_cards = "\n".join(
        card(f"{name} 청소", f"/region/{slugify(name)}/", f"{len(items)}개 페이지")
        for name, items in sorted(regions.items())
    )
    write_file(
        DEPLOYS_DIR / "regions" / "index.html",
        simple_layout(f"{BRAND_NAME} 지역별 청소", "지역별 청소 서비스 목록입니다.", f'<div class="grid">{region_cards}</div>', f"{SITE_URL.rstrip('/')}/regions/")
    )

    service_cards = "\n".join(
        card(name, f"/service/{slugify(name)}/", f"{len(items)}개 페이지")
        for name, items in sorted(services.items())
    )
    write_file(
        DEPLOYS_DIR / "services" / "index.html",
        simple_layout(f"{BRAND_NAME} 서비스별 청소", "서비스별 청소 페이지 목록입니다.", f'<div class="grid">{service_cards}</div>', f"{SITE_URL.rstrip('/')}/services/")
    )

    for region, items in regions.items():
        cards = "\n".join(card(p.keyword, f"/{p.slug}/", p.description[:90]) for p in items)
        slug = slugify(region)
        write_file(
            DEPLOYS_DIR / "region" / slug / "index.html",
            simple_layout(f"{region} 청소 서비스 | {BRAND_NAME}", f"{region} 지역 청소 페이지입니다.", f'<div class="grid">{cards}</div>', f"{SITE_URL.rstrip('/')}/region/{slug}/")
        )

    for service, items in services.items():
        cards = "\n".join(card(p.keyword, f"/{p.slug}/", p.description[:90]) for p in items)
        slug = slugify(service)
        write_file(
            DEPLOYS_DIR / "service" / slug / "index.html",
            simple_layout(f"{service} 전문 안내 | {BRAND_NAME}", f"{service} 관련 청소 페이지입니다.", f'<div class="grid">{cards}</div>', f"{SITE_URL.rstrip('/')}/service/{slug}/")
        )


def xml_urlset(urls: List[str], priority: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    body = "\n".join(f"""  <url>
    <loc>{esc(url)}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{priority}</priority>
  </url>""" for url in urls)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""


def xml_sitemap_index(sitemap_urls: List[str]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    body = "\n".join(f"""  <sitemap>
    <loc>{esc(url)}</loc>
    <lastmod>{today}</lastmod>
  </sitemap>""" for url in sitemap_urls)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</sitemapindex>
"""


def build_sitemaps(pages: List[Page]) -> None:
    main_urls = [
        f"{SITE_URL.rstrip('/')}/",
        f"{SITE_URL.rstrip('/')}/regions/",
        f"{SITE_URL.rstrip('/')}/services/",
    ]
    region_urls = [f"{SITE_URL.rstrip('/')}/region/{slugify(r)}/" for r in sorted(group_by(pages, "region").keys())]
    service_urls = [f"{SITE_URL.rstrip('/')}/service/{slugify(s)}/" for s in sorted(group_by(pages, "service").keys())]
    page_urls = [f"{SITE_URL.rstrip('/')}/{p.slug.strip('/')}/" for p in pages]

    files = []
    write_file(DEPLOYS_DIR / "sitemap-main.xml", xml_urlset(main_urls, "1.0"))
    files.append("sitemap-main.xml")

    write_file(DEPLOYS_DIR / "sitemap-region.xml", xml_urlset(region_urls, "0.7"))
    files.append("sitemap-region.xml")

    write_file(DEPLOYS_DIR / "sitemap-service.xml", xml_urlset(service_urls, "0.7"))
    files.append("sitemap-service.xml")

    for i in range(0, len(page_urls), MAX_URLS_PER_SITEMAP):
        num = i // MAX_URLS_PER_SITEMAP + 1
        name = f"sitemap-pages-{num}.xml"
        write_file(DEPLOYS_DIR / name, xml_urlset(page_urls[i:i + MAX_URLS_PER_SITEMAP], "0.8"))
        files.append(name)

    index_urls = [f"{SITE_URL.rstrip('/')}/{x}" for x in files]
    write_file(DEPLOYS_DIR / "sitemap.xml", xml_sitemap_index(index_urls))
    print("사이트맵 생성 완료:", ", ".join(files))


def build_rss(pages: List[Page]) -> None:
    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0900")
    items = []
    for p in pages[:50]:
        link = f"{SITE_URL.rstrip('/')}/{p.slug}/"
        items.append(
            f"<item><title>{esc(p.title)}</title><link>{esc(link)}</link><guid>{esc(link)}</guid><description>{esc(p.description)}</description><pubDate>{now}</pubDate></item>"
        )

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(BRAND_NAME)} 청소 서비스</title><link>{esc(SITE_URL.rstrip('/') + '/')}</link><description>체인지클린 최신 청소 페이지</description><language>ko-KR</language><lastBuildDate>{now}</lastBuildDate>{''.join(items)}</channel></rss>"""
    write_file(DEPLOYS_DIR / "rss.xml", rss)


def build_robots() -> None:
    write_file(DEPLOYS_DIR / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n")


def validate_sitemap() -> bool:
    path = DEPLOYS_DIR / "sitemap.xml"
    if not path.exists():
        print("sitemap.xml 없음")
        return False

    head = path.read_text(encoding="utf-8", errors="ignore")[:300]
    if not head.startswith("<?xml") or "<sitemapindex" not in head:
        print("sitemap.xml 형식 오류")
        print(head)
        return False

    return True


def run_cmd(cmd: List[str], title: str) -> int:
    print("\n" + "=" * 76)
    print(title)
    print("$ " + " ".join(cmd))
    print("=" * 76)
    result = subprocess.run(cmd, cwd=BASE_DIR, shell=False)
    if result.returncode != 0:
        print(f"오류 발생: {title} / code={result.returncode}")
    return result.returncode


def git_run(command: List[str], dry_run: bool = False) -> Tuple[int, str]:
    if dry_run:
        return 0, "DRY RUN: " + " ".join(command)
    try:
        result = subprocess.run(command, cwd=BASE_DIR, capture_output=True, text=True, shell=False)
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError:
        return 127, "Git이 설치되어 있지 않거나 PATH에 없습니다."


def run_git(message: str, dry_run: bool) -> int:
    for cmd in [["git", "add", "."], ["git", "commit", "-m", message], ["git", "push"]]:
        code, output = git_run(cmd, dry_run)
        print("$", " ".join(cmd))
        if output.strip():
            print(output.strip())
        if code != 0 and "nothing to commit" not in output.lower():
            return code
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="V6 Fixed 원클릭 SEO 배포")
    parser.add_argument("--skip-keywords", action="store_true", help="키워드 생성 건너뛰기")
    parser.add_argument("--limit", type=int, default=0, help="테스트용 페이지 수 제한")
    parser.add_argument("--force", action="store_true", help="전체 강제 재생성")
    parser.add_argument("--no-git", action="store_true", help="Git push 없이 로컬 생성")
    parser.add_argument("--dry-run", action="store_true", help="Git dry-run")
    parser.add_argument("--message", default="", help="Git commit 메시지")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    py = sys.executable

    ensure_templates()

    if not args.skip_keywords and (BASE_DIR / "keyword_engine_v5.py").exists():
        cmd = [py, "keyword_engine_v5.py", "--append"]
        if args.limit:
            cmd += ["--limit", str(args.limit)]
        code = run_cmd(cmd, "1단계: 키워드 생성/중복 제거")
        if code:
            return code
    else:
        print("키워드 생성 건너뜀")

    if not (BASE_DIR / "make_sites_v5.py").exists():
        print("make_sites_v5.py가 없습니다.")
        return 1

    cmd = [py, "make_sites_v5.py"]
    if args.limit:
        cmd += ["--limit", str(args.limit)]
    if args.force:
        cmd += ["--force"]

    code = run_cmd(cmd, "2단계: SEO 페이지 생성")
    if code:
        return code

    pages = get_pages()
    if not pages:
        print("페이지 정보를 찾지 못했습니다.")
        return 1

    print("\n" + "=" * 76)
    print(f"3단계: V6 메인/카테고리/사이트맵/RSS 생성 / 페이지 수: {len(pages)}")
    print("=" * 76)

    build_home_index(pages)
    build_category_pages(pages)
    build_sitemaps(pages)
    build_rss(pages)
    build_robots()

    if not validate_sitemap():
        return 1

    print("V6 사이트 파일 생성 완료")

    if not args.no_git:
        msg = args.message or f"V6 fixed deploy {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        code = run_git(msg, args.dry_run)
        if code:
            return code
    else:
        print("Git 배포는 건너뛰었습니다.")

    print("\n전체 완료")
    print(f"{SITE_URL.rstrip('/')}/")
    print(f"{SITE_URL.rstrip('/')}/sitemap.xml")
    print(f"{SITE_URL.rstrip('/')}/rss.xml")
    print(f"{SITE_URL.rstrip('/')}/robots.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
