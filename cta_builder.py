# -*- coding: utf-8 -*-

from .config import BRAND_NAME, PHONE_TEXT
from .utils import html_escape

def build_cta(keyword, region, service):
    return f"""
<div class="cta">
<strong>{BRAND_NAME} 상담 안내</strong><br>
{html_escape(keyword)} 작업이 필요하시다면 현장 사진과 평수, 희망 날짜를 알려주세요.<br>
{PHONE_TEXT}
</div>
"""
