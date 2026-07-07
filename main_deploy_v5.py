# -*- coding: utf-8 -*-
"""
V5-5 : main_deploy_v5.py
메인 홈페이지/카테고리/자동 Git 배포
"""

from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime

BASE=Path(__file__).resolve().parent
DEPLOYS=BASE/"deploys"
SITE_URL="https://changeclean1.netlify.app"

def page_dirs():
    return sorted([p for p in DEPLOYS.iterdir() if p.is_dir()])

def build_index():
    links=[]
    for p in page_dirs():
        title=p.name.replace("-"," ")
        links.append(f'<li><a href="/{p.name}/">{title}</a></li>')
    html=f"""<!doctype html><html lang="ko"><head>
<meta charset="utf-8"><title>체인지클린</title></head>
<body>
<h1>체인지클린 지역별 청소 서비스</h1>
<ul>{''.join(links)}</ul>
</body></html>"""
    (DEPLOYS/"index.html").write_text(html,encoding="utf-8")

def build_categories():
    regions={}
    for p in page_dirs():
        key=p.name.split("-")[0]
        regions.setdefault(key,[]).append(p.name)
    cat=DEPLOYS/"category"
    cat.mkdir(exist_ok=True)
    for k,v in regions.items():
        items="".join(f'<li><a href="/{x}/">{x}</a></li>' for x in sorted(v))
        (cat/f"{k}.html").write_text(f"<h1>{k}</h1><ul>{items}</ul>",encoding="utf-8")

def build_sitemap():
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    urlset=ET.Element("urlset",xmlns=ns)
    for p in page_dirs():
        u=ET.SubElement(urlset,"url")
        ET.SubElement(u,"loc").text=f"{SITE_URL}/{p.name}/"
        ET.SubElement(u,"lastmod").text=datetime.now().strftime("%Y-%m-%d")
    ET.ElementTree(urlset).write(DEPLOYS/"sitemap.xml",encoding="utf-8",xml_declaration=True)

def build_robots():
    (DEPLOYS/"robots.txt").write_text(
f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n",
encoding="utf-8")

def run_git():
    cmds=[
        ["git","add","."],
        ["git","commit","-m","Auto deploy"],
        ["git","push"]
    ]
    for c in cmds:
        try:
            subprocess.run(c,cwd=BASE,check=False)
        except FileNotFoundError:
            print("Git이 설치되어 있지 않습니다.")
            return

def main():
    DEPLOYS.mkdir(exist_ok=True)
    build_index()
    build_categories()
    build_sitemap()
    build_robots()
    run_git()
    print("V5-5 완료")

if __name__=="__main__":
    main()
