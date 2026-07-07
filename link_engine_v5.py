# -*- coding: utf-8 -*-
"""
V5-4 : link_engine_v5.py
운영용 내부링크 엔진
"""

from collections import defaultdict
from html import escape

MAX_LINKS=8

def _v(v):
    return "" if v is None else str(v).strip()

def generate_links(current, all_rows):
    cur_slug=_v(current.get("slug"))
    cur_region=_v(current.get("region"))
    cur_service=_v(current.get("service"))

    score=[]
    for row in all_rows:
        slug=_v(row.get("slug"))
        if not slug or slug==cur_slug:
            continue
        s=0
        if cur_region and _v(row.get("region"))==cur_region:
            s+=3
        if cur_service and _v(row.get("service"))==cur_service:
            s+=2
        if s==0:
            continue
        score.append((s,row))
    score.sort(key=lambda x:(-x[0],_v(x[1].get("keyword"))))
    links=[]
    used=set()
    for _,row in score:
        slug=_v(row.get("slug"))
        if slug in used:
            continue
        used.add(slug)
        kw=escape(_v(row.get("keyword")))
        links.append(f'<a href="/{slug}/">{kw}</a>')
        if len(links)>=MAX_LINKS:
            break
    if not links:
        return ""
    return "<div class=\"links\"><h2>관련 서비스</h2>"+"".join(links)+"</div>"

def generate_links_map(rows):
    out={}
    dicts=[r if isinstance(r,dict) else vars(r) for r in rows]
    for r in dicts:
        out[_v(r.get("slug"))]=generate_links(r,dicts)
    return out

if __name__=="__main__":
    rows=[
        {"keyword":"서울 강남 입주청소","slug":"gangnam","region":"서울","service":"입주청소"},
        {"keyword":"서울 송파 입주청소","slug":"songpa","region":"서울","service":"입주청소"},
        {"keyword":"인천 입주청소","slug":"incheon","region":"인천","service":"입주청소"},
    ]
    print(generate_links(rows[0],rows))
