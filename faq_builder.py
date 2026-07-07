# -*- coding: utf-8 -*-

from .config import BRAND_NAME
from .utils import html_escape, paragraph

def generate_faqs(keyword, region, service):
    return [
        ("작업 시간은 얼마나 걸리나요?", f"{region} 현장의 크기, 오염도, 작업 범위에 따라 달라집니다. 상담 시 평수와 사진을 알려주시면 더 정확하게 안내할 수 있습니다."),
        ("청소 범위는 어디까지 포함되나요?", f"기본적으로 주방, 욕실, 창틀, 바닥, 수납장 내부 등 생활 공간 중심으로 진행하며 {service} 특성에 따라 세부 범위가 달라질 수 있습니다."),
        ("당일 예약도 가능한가요?", "일정에 여유가 있으면 당일 상담도 가능하지만, 원하는 날짜가 있다면 미리 문의하는 것이 좋습니다."),
        ("추가 비용이 생길 수 있나요?", "심한 곰팡이, 강한 기름때, 특수 오염, 폐기물 처리 등 기본 범위를 벗어나는 작업은 현장 확인 후 안내될 수 있습니다."),
    ]

def build_faq_html(keyword, region, service):
    faqs = generate_faqs(keyword, region, service)
    items = []
    for q, a in faqs:
        items.append(f"{paragraph('<strong>Q. ' + html_escape(q) + '</strong><br>' + html_escape(a))}")
    return f"""
<section>
<h2>자주 묻는 질문</h2>
{''.join(items)}
</section>
"""
