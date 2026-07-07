"""
keyword_parser_v4.py
키워드에서 지역/서비스/건물/의도/평수 등을 추출합니다.
"""

from __future__ import annotations

import re
from typing import Dict


SERVICES = [
    "입주청소", "이사청소", "거주청소", "준공청소",
    "상가청소", "사무실청소", "공장청소", "원룸청소",
]

BUILDINGS = [
    "아파트", "빌라", "원룸", "오피스텔", "단독주택",
    "상가", "사무실", "공장", "신축", "구축",
]

INTENTS = [
    "잘하는 곳", "전문업체", "추천", "비용", "가격", "후기",
    "당일", "24시간", "청소업체", "곰팡이 제거", "새집증후군",
]

REMOVE_WORDS = [
    "전문업체", "청소업체", "잘하는 곳", "추천", "비용", "가격", "후기", "당일", "24시간"
]


def find_first(text: str, words: list[str]) -> str:
    for w in words:
        if w in text:
            return w
    return ""


def find_pyeong(text: str) -> str:
    m = re.search(r"(\d{1,3})\s*평", text)
    return f"{m.group(1)}평" if m else ""


def parse_keyword(keyword: str) -> Dict[str, str]:
    keyword = (keyword or "").strip()

    service = find_first(keyword, SERVICES)
    building = find_first(keyword, BUILDINGS)
    intent = find_first(keyword, INTENTS)
    pyeong = find_pyeong(keyword)

    area = keyword

    for token in [service, building, intent, pyeong]:
        if token:
            area = area.replace(token, "")

    for word in REMOVE_WORDS:
        area = area.replace(word, "")

    area = re.sub(r"\s+", " ", area).strip()

    return {
        "keyword": keyword,
        "area": area,
        "service": service or "청소",
        "building": building,
        "intent": intent,
        "pyeong": pyeong,
    }


if __name__ == "__main__":
    print(parse_keyword("인천 숭의동 아파트 이사청소 잘하는 곳"))
