# -*- coding: utf-8 -*-

from .utils import clean_text

def keyword_density_score(content, keyword):
    content = clean_text(content)
    keyword = clean_text(keyword)
    if not content or not keyword:
        return 0
    return content.count(keyword)

def ensure_keyword_presence(content, keyword):
    if keyword and keyword not in content:
        return f"<p>{keyword} 관련 상담과 작업 범위를 자세히 안내드립니다.</p>\n" + content
    return content
