"""
link_engine_v4_1.py

v4.1 속도개선 내부링크 엔진
- 지역별/서비스별 인덱스를 한 번만 생성
- 각 페이지마다 전체 페이지를 반복 비교하지 않음
"""

from __future__ import annotations

import html
import random
from collections import defaultdict
from typing import Dict, List, Any


def esc(v: str) -> str:
    return html.escape(str(v or ""), quote=True)


def norm(v: str) -> str:
    return str(v or "").replace(" ", "").strip()


def make_page_record(keyword: str, slug: str, parsed: Dict[str, str]) -> Dict[str, str]:
    return {
        "keyword": keyword,
        "slug": slug,
        "area": parsed.get("area", ""),
        "service": parsed.get("service", ""),
        "building": parsed.get("building", ""),
        "intent": parsed.get("intent", ""),
        "pyeong": parsed.get("pyeong", ""),
    }


def url(base_url: str, slug: str) -> str:
    return f"{base_url.rstrip('/')}/{slug.strip('/')}/"


def build_link_index(pages: List[Dict[str, str]]) -> Dict[str, Any]:
    by_area = defaultdict(list)
    by_service = defaultdict(list)

    for p in pages:
        area_key = norm(p.get("area", ""))
        service_key = p.get("service", "").strip()

        if area_key:
            by_area[area_key].append(p)

        if service_key:
            by_service[service_key].append(p)

    return {
        "by_area": dict(by_area),
        "by_service": dict(by_service),
    }


def pick_unique(
    current: Dict[str, str],
    candidates: List[Dict[str, str]],
    already: set,
    limit: int,
) -> List[Dict[str, str]]:
    out = []

    if not candidates:
        return out

    sample = candidates[:]
    random.shuffle(sample)

    for p in sample:
        slug = p.get("slug", "")
        if not slug or slug == current.get("slug") or slug in already:
            continue

        out.append(p)
        already.add(slug)

        if len(out) >= limit:
            break

    return out


def related_fast(
    current: Dict[str, str],
    pages: List[Dict[str, str]],
    index: Dict[str, Any],
    limit: int = 10,
) -> List[Dict[str, str]]:
    area_key = norm(current.get("area", ""))
    service_key = current.get("service", "").strip()

    by_area = index.get("by_area", {})
    by_service = index.get("by_service", {})

    selected = []
    already = set()

    # 1순위: 같은 지역
    area_candidates = by_area.get(area_key, [])
    picked = pick_unique(current, area_candidates, already, max(4, limit // 2))
    selected.extend(picked)

    # 2순위: 같은 서비스
    remain = limit - len(selected)
    if remain > 0:
        service_candidates = by_service.get(service_key, [])
        picked = pick_unique(current, service_candidates, already, remain)
        selected.extend(picked)

    # 3순위: 전체에서 일부만 랜덤 샘플링
    remain = limit - len(selected)
    if remain > 0 and pages:
        sample_size = min(300, len(pages))
        random_candidates = random.sample(pages, sample_size)
        picked = pick_unique(current, random_candidates, already, remain)
        selected.extend(picked)

    return selected[:limit]


def links_html(
    current: Dict[str, str],
    pages: List[Dict[str, str]],
    index: Dict[str, Any],
    base_url: str,
    limit: int = 10,
) -> str:
    rel = related_fast(current, pages, index, limit)
    if not rel:
        return ""

    out = ["<section class='related-links'><h2>함께 보면 좋은 청소 서비스</h2><ul>"]

    for p in rel:
        out.append(f'<li><a href="{esc(url(base_url, p["slug"]))}">{esc(p["keyword"])}</a></li>')

    out.append("</ul></section>")
    return "\n".join(out)


def prev_next_html(current: Dict[str, str], pages: List[Dict[str, str]], base_url: str) -> str:
    # 7만개에서 index 찾기 반복을 줄이기 위해 slug_index가 없으면 단순 fallback
    # prev/next는 필수 아님. 그래도 사용성을 위해 샘플 연결 제공.
    try:
        current_slug = current.get("slug", "")
        idx = next(i for i, p in enumerate(pages) if p.get("slug") == current_slug)
    except StopIteration:
        return ""

    out = ["<nav class='prev-next-links'>"]

    if idx > 0:
        p = pages[idx - 1]
        out.append(f'<a href="{esc(url(base_url, p["slug"]))}">← {esc(p["keyword"])}</a>')

    if idx < len(pages) - 1:
        p = pages[idx + 1]
        out.append(f'<a href="{esc(url(base_url, p["slug"]))}">{esc(p["keyword"])} →</a>')

    out.append("</nav>")
    return "\n".join(out)


def build_link_pack_fast(
    current: Dict[str, str],
    pages: List[Dict[str, str]],
    index: Dict[str, Any],
    base_url: str,
) -> Dict[str, str]:
    h = links_html(current, pages, index, base_url)
    pn = prev_next_html(current, pages, base_url)

    return {
        "{{내부링크}}": h,
        "{{관련링크}}": h,
        "{{지역링크}}": h,
        "{{이전다음링크}}": pn,
    }
