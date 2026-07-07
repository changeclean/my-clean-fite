# -*- coding: utf-8 -*-
"""
V5-3 콘텐츠 엔진 메인
make_sites_v5.py가 호출하는 핵심 함수:
    generate_content(row)
"""

from __future__ import annotations

from .utils import clean_text, infer_region, infer_service
from .paragraph_builder import (
    build_intro,
    build_process,
    build_reason,
    build_checkpoints,
    build_finish,
)
from .faq_builder import build_faq_html, generate_faqs
from .cta_builder import build_cta
from .keyword_optimizer import ensure_keyword_presence
from .duplicate_filter import remove_duplicate_paragraphs

def generate_content(row):
    """
    row는 dict 또는 PageRow dataclass의 asdict 결과를 받습니다.
    필수/권장 키:
    - keyword
    - region
    - service
    - category
    """
    if not isinstance(row, dict):
        try:
            row = dict(row)
        except Exception:
            row = {}

    keyword = clean_text(row.get("keyword", ""))
    region = infer_region(keyword, clean_text(row.get("region", "")))
    service = infer_service(keyword, clean_text(row.get("service", "")))

    html = "\n".join([
        build_intro(keyword, region, service),
        build_process(keyword, region, service),
        build_checkpoints(keyword, region, service),
        build_reason(keyword, region, service),
        build_faq_html(keyword, region, service),
        build_finish(keyword, region, service),
        build_cta(keyword, region, service),
    ])

    html = ensure_keyword_presence(html, keyword)
    html = remove_duplicate_paragraphs(html)
    return html

def generate_full_content(row):
    return generate_content(row)

def get_faqs(row):
    if not isinstance(row, dict):
        row = {}
    keyword = clean_text(row.get("keyword", ""))
    region = infer_region(keyword, clean_text(row.get("region", "")))
    service = infer_service(keyword, clean_text(row.get("service", "")))
    return generate_faqs(keyword, region, service)

# seo_engine_v5에서 필요할 때 쓸 수 있도록 별칭 제공
generate_faqs_for_schema = get_faqs
