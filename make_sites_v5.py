# -*- coding: utf-8 -*-
"""
V5-1 : make_sites_v5.py
생성 엔진 (초기 골격)

기능
- keywords.xlsx 읽기
- deploys/slug/index.html 생성
- 변경된 페이지만 재생성(MD5 캐시)
- report_v5.csv 생성
"""

from pathlib import Path
import hashlib
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
KEYWORD_FILE = BASE_DIR / "keywords.xlsx"
TEMPLATE_FILE = BASE_DIR / "template.html"
OUTPUT_DIR = BASE_DIR / "deploys"
CACHE_DIR = BASE_DIR / ".cache"
CACHE_FILE = CACHE_DIR / "page_hash_v5.json"
REPORT_FILE = BASE_DIR / "report_v5.csv"

OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

def md5(text:str)->str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_template():
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESCRIPTION}}">
</head>
<body>
<h1>{{H1}}</h1>
{{CONTENT}}
</body>
</html>"""

def build_html(row, template):
    html = template
    html = html.replace("{{TITLE}}", str(row.get("title", row["keyword"])))
    html = html.replace("{{DESCRIPTION}}", str(row.get("description", row["keyword"])))
    html = html.replace("{{H1}}", str(row.get("h1", row["keyword"])))
    html = html.replace("{{CONTENT}}", str(row.get("content", "")))
    return html

def main():
    df = pd.read_excel(KEYWORD_FILE)
    cache = load_cache()
    template = load_template()
    report = []

    for _, row in df.iterrows():
        slug = str(row["slug"]).strip()
        html = build_html(row, template)
        h = md5(html)

        if cache.get(slug) == h:
            report.append({"slug": slug, "status": "SKIP"})
            continue

        folder = OUTPUT_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(html, encoding="utf-8")

        cache[slug] = h
        report.append({"slug": slug, "status": "UPDATED"})

    save_cache(cache)
    pd.DataFrame(report).to_csv(REPORT_FILE, index=False, encoding="utf-8-sig")
    print("완료:", len(report), "페이지")

if __name__ == "__main__":
    main()
