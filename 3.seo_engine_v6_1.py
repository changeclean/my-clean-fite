#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3.seo_engine_v6_1.py

V6.1 SEO 메타데이터 생성 엔진

기능
- 롱테일 키워드에 맞는 title / description / h1 생성
- canonical URL 생성
- Open Graph / Twitter 메타데이터 생성
- LocalBusiness + Service + BreadcrumbList JSON-LD 생성
- 과도한 "전문업체", "잘하는 곳" 반복 최소화
- 2.make_sites_v6_1.py에서 import하여 사용 가능

단독 테스트:
    python 3.seo_engine_v6_1.py \
      --keyword "인천 계양구 아파트 에어컨 실외기실 비둘기 똥 청소" \
      --slug "incheon-gyeyang-apartment-outdoor-unit-room-cleaning"
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict


SITE_URL = "https://changeclean1.netlify.app"
BRAND_NAME = "체인지클린"
PHONE_NUMBER = "1688-6751"
DEFAULT_IMAGE = f"{SITE_URL}/images/M2.jpg"


@dataclass(frozen=True)
class SeoData:
    keyword: str
    slug: str
    title: str
    description: str
    h1: str
    canonical: str
    robots: str
    og: Dict[str, str]
    twitter: Dict[str, str]
    schema: str


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_slug(value: str) -> str:
    slug = clean(value).lower().replace("\\", "/").strip("/")
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9가-힣/_-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = re.sub(r"/{2,}", "/", slug)
    return slug.strip("-/")


def trim_text(text: str, limit: int) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    shortened = text[:limit].rstrip(" ,.-|/")
    return shortened


def infer_service(keyword: str, service: str = "") -> str:
    if clean(service):
        return clean(service)

    candidates = [
        "입주청소",
        "이사청소",
        "거주청소",
        "상가청소",
        "사무실청소",
        "폐기물청소",
        "원룸청소",
        "아파트청소",
        "빌라청소",
        "공장청소",
        "창고청소",
        "특수청소",
    ]
    compact = clean(keyword).replace(" ", "")
    for item in candidates:
        if item in compact:
            return item
    return "청소"


def infer_region(keyword: str, region: str = "") -> str:
    if clean(region):
        return clean(region)

    words = clean(keyword).split()
    if not words:
        return "해당 지역"

    metro = {"서울", "서울시", "인천", "인천시", "경기", "경기도"}
    if len(words) >= 2 and words[0] in metro:
        return f"{words[0]} {words[1]}"
    return words[0]


def build_title(keyword: str, brand: str = BRAND_NAME) -> str:
    keyword = clean(keyword)
    brand = clean(brand) or BRAND_NAME

    # 검색어 자체가 길기 때문에 불필요한 광고성 수식어를 추가하지 않습니다.
    suffix = f" | {brand}"
    return trim_text(keyword + suffix, 60)


def build_description(
    keyword: str,
    region: str = "",
    service: str = "",
    brand: str = BRAND_NAME,
) -> str:
    keyword = clean(keyword)
    region = infer_region(keyword, region)
    service = infer_service(keyword, service)
    brand = clean(brand) or BRAND_NAME

    description = (
        f"{keyword} 작업 범위와 진행 순서, 견적 전 확인사항을 안내합니다. "
        f"{region} {service} 현장의 구조와 오염 상태를 확인해 필요한 구역을 중심으로 작업하는 {brand}입니다."
    )
    return trim_text(description, 155)


def build_h1(keyword: str) -> str:
    return trim_text(clean(keyword), 90)


def build_canonical(slug: str, site_url: str = SITE_URL) -> str:
    safe_slug = clean_slug(slug)
    base = clean(site_url).rstrip("/")
    return f"{base}/{safe_slug}/" if safe_slug else f"{base}/"


def build_og(title: str, description: str, canonical: str, image: str = DEFAULT_IMAGE) -> Dict[str, str]:
    return {
        "og:locale": "ko_KR",
        "og:type": "article",
        "og:site_name": BRAND_NAME,
        "og:title": title,
        "og:description": description,
        "og:url": canonical,
        "og:image": clean(image) or DEFAULT_IMAGE,
    }


def build_twitter(title: str, description: str, image: str = DEFAULT_IMAGE) -> Dict[str, str]:
    return {
        "twitter:card": "summary_large_image",
        "twitter:title": title,
        "twitter:description": description,
        "twitter:image": clean(image) or DEFAULT_IMAGE,
    }


def build_schema(
    keyword: str,
    canonical: str,
    description: str,
    region: str = "",
    service: str = "",
    image: str = DEFAULT_IMAGE,
) -> str:
    keyword = clean(keyword)
    region = infer_region(keyword, region)
    service = infer_service(keyword, service)

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LocalBusiness",
                "@id": f"{SITE_URL.rstrip('/')}#business",
                "name": BRAND_NAME,
                "url": SITE_URL.rstrip("/") + "/",
                "telephone": PHONE_NUMBER,
                "image": clean(image) or DEFAULT_IMAGE,
                "areaServed": {
                    "@type": "AdministrativeArea",
                    "name": region,
                },
            },
            {
                "@type": "Service",
                "@id": canonical + "#service",
                "name": keyword,
                "serviceType": service,
                "description": description,
                "url": canonical,
                "provider": {"@id": f"{SITE_URL.rstrip('/')}#business"},
                "areaServed": {
                    "@type": "AdministrativeArea",
                    "name": region,
                },
            },
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "홈",
                        "item": SITE_URL.rstrip("/") + "/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": region,
                        "item": f"{SITE_URL.rstrip('/')}/regions/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": keyword,
                        "item": canonical,
                    },
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2)


def generate(
    keyword: str,
    slug: str,
    region: str = "",
    service: str = "",
    image: str = DEFAULT_IMAGE,
    site_url: str = SITE_URL,
    brand: str = BRAND_NAME,
) -> Dict[str, Any]:
    keyword = clean(keyword)
    slug = clean_slug(slug)

    if not keyword:
        raise ValueError("keyword 값이 비어 있습니다.")
    if not slug:
        raise ValueError("slug 값이 비어 있습니다.")

    resolved_region = infer_region(keyword, region)
    resolved_service = infer_service(keyword, service)
    title = build_title(keyword, brand)
    description = build_description(keyword, resolved_region, resolved_service, brand)
    h1 = build_h1(keyword)
    canonical = build_canonical(slug, site_url)

    data = SeoData(
        keyword=keyword,
        slug=slug,
        title=title,
        description=description,
        h1=h1,
        canonical=canonical,
        robots="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
        og=build_og(title, description, canonical, image),
        twitter=build_twitter(title, description, image),
        schema=build_schema(
            keyword=keyword,
            canonical=canonical,
            description=description,
            region=resolved_region,
            service=resolved_service,
            image=image,
        ),
    )
    return asdict(data)


def meta_tags(seo: Dict[str, Any]) -> str:
    """template.html의 {{SEO_META}}에 삽입 가능한 메타 태그 묶음."""
    lines = [
        f'<meta name="description" content="{seo["description"]}">',
        f'<meta name="robots" content="{seo["robots"]}">',
        f'<link rel="canonical" href="{seo["canonical"]}">',
    ]

    for name, value in seo.get("og", {}).items():
        lines.append(f'<meta property="{name}" content="{value}">')
    for name, value in seo.get("twitter", {}).items():
        lines.append(f'<meta name="{name}" content="{value}">')

    lines.append('<script type="application/ld+json">')
    lines.append(seo["schema"])
    lines.append("</script>")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="V6.1 SEO 메타데이터 생성 테스트")
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--region", default="")
    parser.add_argument("--service", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = generate(
        keyword=args.keyword,
        slug=args.slug,
        region=args.region,
        service=args.service,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
