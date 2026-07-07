# -*- coding: utf-8 -*-

import re
from html import escape

def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()

def html_escape(value):
    return escape(clean_text(value), quote=True)

def normalize_space(text):
    return re.sub(r"\s+", " ", clean_text(text)).strip()

def infer_service(keyword, service=""):
    if service:
        return service
    keyword = clean_text(keyword)
    candidates = ["입주청소", "이사청소", "사무실청소", "상가청소", "빌라청소", "아파트청소", "준공청소", "거주청소", "화장실청소", "주방청소"]
    for item in candidates:
        if item in keyword:
            return item
    return "전문청소"

def infer_region(keyword, region=""):
    if region:
        return region
    words = clean_text(keyword).split()
    if not words:
        return "해당 지역"
    if len(words) >= 2 and words[0] in ["서울", "경기", "인천"]:
        return f"{words[0]} {words[1]}"
    return words[0]

def paragraph(text):
    return f"<p>{text}</p>"
