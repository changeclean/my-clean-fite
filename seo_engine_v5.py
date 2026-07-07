# -*- coding: utf-8 -*-
"""
V5-2 : seo_engine_v5.py
"""

from html import escape

SITE_URL = "https://changeclean1.netlify.app"

def build_title(keyword: str) -> str:
    return f"{keyword} | 체인지클린"

def build_description(keyword: str) -> str:
    return (
        f"{keyword} 전문업체 체인지클린. "
        "입주청소, 이사청소, 상가청소, 사무실청소까지 합리적인 가격으로 진행합니다."
    )[:155]

def build_h1(keyword: str) -> str:
    return keyword

def build_canonical(slug: str) -> str:
    return f"{SITE_URL}/{slug}/"

def build_og(title: str, description: str, canonical: str) -> dict:
    return {
        "og:title": title,
        "og:description": description,
        "og:type": "website",
        "og:url": canonical,
    }

def build_schema(keyword: str, canonical: str) -> str:
    return """{
  "@context":"https://schema.org",
  "@type":"LocalBusiness",
  "name":"체인지클린",
  "url":"%s",
  "description":"%s 전문 청소 서비스"
}""" % (escape(canonical), escape(keyword))

def generate(keyword: str, slug: str) -> dict:
    title = build_title(keyword)
    description = build_description(keyword)
    h1 = build_h1(keyword)
    canonical = build_canonical(slug)

    return {
        "title": title,
        "description": description,
        "h1": h1,
        "canonical": canonical,
        "og": build_og(title, description, canonical),
        "schema": build_schema(keyword, canonical),
    }

if __name__ == "__main__":
    import pprint
    pprint.pprint(generate("서울 용산구 입주청소","seoul-yongsan-move-in-cleaning"))
