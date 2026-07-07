"""
sitemap_engine_v4.py
sitemap.xml / sitemap index / robots.txt 생성
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List


LIMIT = 50000


def page_url(base_url: str, slug: str) -> str:
    return f"{base_url.rstrip('/')}/{slug.strip('/')}/"


def sitemap_xml(urls: List[str]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        out.append("  <url>")
        out.append(f"    <loc>{u}</loc>")
        out.append(f"    <lastmod>{today}</lastmod>")
        out.append("    <changefreq>weekly</changefreq>")
        out.append("    <priority>0.8</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out)


def sitemap_index_xml(urls: List[str]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        out.append("  <sitemap>")
        out.append(f"    <loc>{u}</loc>")
        out.append(f"    <lastmod>{today}</lastmod>")
        out.append("  </sitemap>")
    out.append("</sitemapindex>")
    return "\n".join(out)


def chunks(items: List[str], size: int):
    for i in range(0, len(items), size):
        yield items[i:i+size]


def generate_all_sitemaps(output_dir: str | Path, pages: List[Dict[str, str]], base_url: str) -> None:
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    urls = [page_url(base_url, p["slug"]) for p in pages if p.get("slug")]

    if len(urls) <= LIMIT:
        (out / "sitemap.xml").write_text(sitemap_xml(urls), encoding="utf-8")
    else:
        sitemap_urls = []
        for idx, chunk in enumerate(chunks(urls, LIMIT), start=1):
            name = f"sitemap-{idx}.xml"
            (out / name).write_text(sitemap_xml(chunk), encoding="utf-8")
            sitemap_urls.append(f"{base_url.rstrip('/')}/{name}")
        (out / "sitemap.xml").write_text(sitemap_index_xml(sitemap_urls), encoding="utf-8")

    robots = f"""User-agent: *
Allow: /

Sitemap: {base_url.rstrip('/')}/sitemap.xml
"""
    (out / "robots.txt").write_text(robots, encoding="utf-8")
