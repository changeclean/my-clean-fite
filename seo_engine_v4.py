"""
seo_engine_v4.py
SEO Head / FAQ / Schema 생성
"""

from __future__ import annotations

import html
import json
from datetime import date
from typing import Dict, List


BRAND = "체인지클린"
PHONE = "1688-6751"


def esc(v: str) -> str:
    return html.escape(str(v or ""), quote=True)


def canonical(base_url: str, slug: str) -> str:
    return f"{base_url.rstrip('/')}/{slug.strip('/')}/"


def title(page: Dict[str, str]) -> str:
    return f"{page.get('keyword','').strip()}｜{BRAND}"


def description(page: Dict[str, str]) -> str:
    area = page.get("area") or "서울 경기 인천"
    service = page.get("service") or "청소"
    building = page.get("building") or ""
    intent = page.get("intent") or ""

    desc = f"{area} {building} {service} 전문업체 {BRAND}. "
    if intent in ["비용", "가격"]:
        desc += "합리적인 비용과 현장 맞춤 상담을 안내합니다. "
    elif intent == "후기":
        desc += "현장 중심의 꼼꼼한 작업 후기를 확인하세요. "
    else:
        desc += "입주청소, 이사청소, 거주청소를 꼼꼼하게 진행합니다. "
    desc += f"빠른상담 {PHONE}"
    return desc[:155]


def faq_items(page: Dict[str, str]) -> List[Dict[str, str]]:
    area = page.get("area") or "해당 지역"
    service = page.get("service") or "청소"
    building = page.get("building") or "공간"
    pyeong = page.get("pyeong") or "평수"

    target = f"{area} {building} {service}".replace("  ", " ").strip()

    return [
        {"q": f"{target} 범위는 어디까지인가요?", "a": "실내 전체, 주방, 욕실, 창틀, 베란다, 수납장 내부, 바닥 등을 현장 상태에 맞춰 진행합니다."},
        {"q": f"{area} {service} 비용은 어떻게 정해지나요?", "a": "평수, 오염도, 구조, 작업 범위, 옵션 유무에 따라 달라집니다. 사진과 주소를 알려주시면 더 정확한 상담이 가능합니다."},
        {"q": f"{pyeong} {service} 작업 시간은 얼마나 걸리나요?", "a": "일반적으로 반나절에서 하루 정도 소요되며, 오염도와 구조에 따라 달라질 수 있습니다."},
        {"q": f"{area} 당일 {service}도 가능한가요?", "a": "예약 상황에 따라 당일 진행이 가능한 경우도 있으니 빠른 일정은 전화 상담을 권장합니다."},
        {"q": "청소 후 검수도 해주시나요?", "a": "작업 완료 후 주요 구역을 다시 확인하고 부족한 부분은 현장에서 보완합니다."},
    ]


def faq_html(page: Dict[str, str]) -> str:
    out = ["<section class='faq-section'><h2>자주 묻는 질문</h2>"]
    for item in faq_items(page):
        out.append(f"<div class='faq-item'><h3>Q. {esc(item['q'])}</h3><p>A. {esc(item['a'])}</p></div>")
    out.append("</section>")
    return "\n".join(out)


def schema_html(page: Dict[str, str], base_url: str) -> str:
    url = canonical(base_url, page["slug"])
    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": BRAND,
            "url": url,
            "telephone": PHONE,
            "areaServed": page.get("area") or "서울 경기 인천",
            "serviceType": page.get("keyword") or page.get("service") or "청소",
            "description": description(page),
            "priceRange": "상담 후 안내",
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}}
                for x in faq_items(page)
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "홈", "item": "https://changeclean.co.kr/"},
                {"@type": "ListItem", "position": 2, "name": "지역청소", "item": base_url.rstrip("/") + "/"},
                {"@type": "ListItem", "position": 3, "name": page.get("keyword",""), "item": url},
            ],
        },
    ]

    return "\n".join(
        '<script type="application/ld+json">\n'
        + json.dumps(s, ensure_ascii=False, indent=2)
        + "\n</script>"
        for s in schemas
    )


def build_seo_pack(page: Dict[str, str], base_url: str) -> Dict[str, str]:
    t = title(page)
    d = description(page)
    c = canonical(base_url, page["slug"])

    head = f"""<title>{esc(t)}</title>
<meta name="description" content="{esc(d)}">
<link rel="canonical" href="{esc(c)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(t)}">
<meta property="og:description" content="{esc(d)}">
<meta property="og:url" content="{esc(c)}">
<meta property="og:site_name" content="{esc(BRAND)}">
<meta name="twitter:card" content="summary_large_image">
{schema_html(page, base_url)}"""

    return {
        "{{SEO_HEAD}}": head,
        "{{TITLE}}": t,
        "{{메타설명}}": d,
        "{{CANONICAL}}": c,
        "{{FAQ}}": faq_html(page),
        "{{SCHEMA}}": schema_html(page, base_url),
        "{{오늘날짜}}": date.today().strftime("%Y-%m-%d"),
    }
