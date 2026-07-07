# -*- coding: utf-8 -*-

from .config import BRAND_NAME
from .utils import html_escape, paragraph

def build_intro(keyword, region, service):
    k = html_escape(keyword); r = html_escape(region); s = html_escape(service)
    return f"""
<section>
<h2>{k} 서비스 안내</h2>
{paragraph(f"{k}는 단순히 눈에 보이는 먼지만 닦는 작업이 아니라 공간의 사용 목적, 오염 상태, 마감재 특성까지 함께 확인해야 하는 작업입니다. 특히 {r} 현장은 아파트, 빌라, 오피스텔, 상가 등 구조가 다양하기 때문에 같은 {s}라도 필요한 작업 순서가 달라질 수 있습니다.")}
{paragraph(f"{BRAND_NAME}은 현장 상황을 먼저 파악하고 주방, 욕실, 창틀, 바닥, 수납장 내부처럼 고객이 실제로 체감하는 구역을 중심으로 꼼꼼하게 점검합니다.")}
</section>
"""

def build_process(keyword, region, service):
    k = html_escape(keyword); r = html_escape(region); s = html_escape(service)
    return f"""
<section>
<h2>{r} {s} 작업 과정</h2>
{paragraph(f"작업은 현장 확인, 오염도 체크, 장비 준비, 구역별 청소, 마무리 검수 순서로 진행됩니다. {k} 작업에서는 공사 분진, 생활 먼지, 물때, 기름때, 창틀 오염처럼 구역별로 다른 오염을 분리해서 접근하는 것이 중요합니다.")}
{paragraph("욕실은 수전 주변과 배수구, 타일 틈새를 확인하고 주방은 후드, 싱크대, 상하부장, 벽면 기름기를 중심으로 살펴봅니다. 바닥과 창틀은 먼지가 다시 날리지 않도록 순서를 맞춰 작업합니다.")}
</section>
"""

def build_reason(keyword, region, service):
    k = html_escape(keyword)
    return f"""
<section>
<h2>{BRAND_NAME}을 선택하는 이유</h2>
{paragraph(f"{k}를 맡길 때 가장 중요한 부분은 빠른 작업보다 결과의 균일함입니다. 작업자가 어떤 기준으로 확인하고 반복 작업하는지에 따라 청소 후 체감 차이가 크게 나타납니다.")}
{paragraph(f"{BRAND_NAME}은 현장별 체크 포인트를 기준으로 작업하고, 고객이 놓치기 쉬운 틈새와 모서리까지 확인하는 방식을 지향합니다. 상담 단계에서도 작업 범위와 추가 확인이 필요한 부분을 쉽게 안내합니다.")}
</section>
"""

def build_checkpoints(keyword, region, service):
    r = html_escape(region); s = html_escape(service)
    return f"""
<section>
<h2>{r}에서 {s}를 맡기기 전 체크사항</h2>
{paragraph("청소를 맡기기 전에는 평수, 공간 구조, 오염 정도, 짐 유무, 엘리베이터 사용 가능 여부를 미리 정리해두면 상담이 훨씬 정확해집니다.")}
{paragraph("특히 신축이나 리모델링 후에는 분진이 수납장 내부와 창틀 하단까지 남는 경우가 많고, 오래 거주한 공간은 욕실 요석과 주방 기름때가 강하게 남을 수 있습니다.")}
</section>
"""

def build_finish(keyword, region, service):
    k = html_escape(keyword)
    return f"""
<section>
<h2>{k} 상담 안내</h2>
{paragraph(f"{k}가 필요하다면 현장 사진, 평수, 원하는 작업 날짜를 함께 알려주시면 상담이 더 빠르게 진행됩니다.")}
{paragraph(f"{BRAND_NAME}은 무리한 안내보다 실제 현장에 맞는 작업 범위와 합리적인 방향을 기준으로 상담합니다.")}
</section>
"""
