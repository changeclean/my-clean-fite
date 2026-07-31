# -*- coding: utf-8 -*-
"""
V6.1 : keyword_engine_v6_1.py

3,000개 기준 롱테일 SEO 키워드 생성 엔진

구성 비율
- 50% : 지역 + 상황/공간 + 서비스
- 25% : 지역 + 평형/주거형태 + 서비스 + 비용 의도
- 15% : 지역 + 오염/문제 해결형
- 10% : 지역 + 서비스 + 전문업체/잘하는곳/가격/비용/견적

기존 파이프라인 호환 컬럼
keyword, slug, region, service, category, title, description, h1

기본 실행(기존 파일에 중복 없이 3,000개 추가):
    python keyword_engine_v6_1.py

정확히 새 3,000개로 교체:
    python keyword_engine_v6_1.py --replace --limit 3000

기존 파일에 3,000개 추가:
    python keyword_engine_v6_1.py --append --limit 3000

테스트:
    python keyword_engine_v6_1.py --replace --limit 100 --output keywords_test.xlsx
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

try:
    import pandas as pd
except ImportError:
    pd = None


BASE_DIR = Path(__file__).resolve().parent
FALLBACK_CSV = BASE_DIR / "keywords.csv"

BRAND_NAME = "체인지클린"
DEFAULT_LIMIT = 3000
DEFAULT_SEED = 20260731


REGIONS: List[Tuple[str, str]] = [
    # 서울
    ("서울", "강남구"), ("서울", "서초구"), ("서울", "송파구"), ("서울", "강동구"),
    ("서울", "마포구"), ("서울", "용산구"), ("서울", "성동구"), ("서울", "광진구"),
    ("서울", "동작구"), ("서울", "관악구"), ("서울", "영등포구"), ("서울", "구로구"),
    ("서울", "금천구"), ("서울", "양천구"), ("서울", "강서구"), ("서울", "은평구"),
    ("서울", "서대문구"), ("서울", "종로구"), ("서울", "중구"), ("서울", "동대문구"),
    ("서울", "중랑구"), ("서울", "성북구"), ("서울", "강북구"), ("서울", "도봉구"),
    ("서울", "노원구"),

    # 인천
    ("인천", "미추홀구"), ("인천", "연수구"), ("인천", "남동구"), ("인천", "부평구"),
    ("인천", "계양구"), ("인천", "서구"), ("인천", "중구"), ("인천", "동구"),
    ("인천", "강화군"),

    # 경기
    ("경기", "수원시"), ("경기", "성남시"), ("경기", "용인시"), ("경기", "고양시"),
    ("경기", "부천시"), ("경기", "안산시"), ("경기", "안양시"), ("경기", "남양주시"),
    ("경기", "화성시"), ("경기", "평택시"), ("경기", "의정부시"), ("경기", "시흥시"),
    ("경기", "파주시"), ("경기", "김포시"), ("경기", "광명시"), ("경기", "광주시"),
    ("경기", "군포시"), ("경기", "하남시"), ("경기", "오산시"), ("경기", "이천시"),
    ("경기", "안성시"), ("경기", "의왕시"), ("경기", "양주시"), ("경기", "구리시"),
    ("경기", "포천시"), ("경기", "여주시"), ("경기", "동두천시"), ("경기", "과천시"),

    # 주요 검색 지역명
    ("경기", "김포"), ("경기", "부천"), ("경기", "고양"), ("경기", "일산"),
]


SERVICES = [
    "입주청소",
    "이사청소",
    "거주청소",
    "원룸청소",
    "아파트청소",
    "빌라청소",
    "오피스텔청소",
    "상가청소",
    "사무실청소",
    "준공청소",
    "폐기물청소",
]


SERVICE_SITUATIONS: Dict[str, Sequence[str]] = {
    "입주청소": [
        "신축 아파트 입주 전", "입주 전 창틀 먼지", "입주 전 주방 수납장",
        "입주 전 화장실 물때", "입주 전 베란다 분진", "입주 전 붙박이장 먼지",
        "입주 전 드레스룸 시스템행거", "입주 전 다용도실 배수구",
        "새집 시멘트가루 제거", "리모델링 후 입주 전",
    ],
    "이사청소": [
        "이사 전 빈집 전체", "이사 후 남은 먼지", "이사 전 주방 기름때",
        "이사 전 욕실 물때", "이사 전 창틀 레일", "이사 전 베란다",
        "이사 전 붙박이장 내부", "이사 전 냉장고 자리", "이사 전 세탁기 자리",
        "이사 당일 빈집",
    ],
    "거주청소": [
        "거주 중 주방 기름때", "거주 중 욕실 물때", "거주 중 베란다 먼지",
        "거주 중 창틀 먼지", "아이 있는 집 전체", "반려동물 있는 집",
        "맞벌이 가정 정기", "명절 전 대청소", "여름철 실외기실",
        "겨울철 결로 곰팡이",
    ],
    "원룸청소": [
        "원룸 입주 전", "원룸 이사 전", "원룸 퇴실 전", "원룸 주방 기름때",
        "원룸 욕실 물때", "원룸 창틀 먼지", "원룸 담배 냄새",
        "원룸 냉장고 내부", "원룸 옵션 가전", "원룸 폐기물 정리 후",
    ],
    "아파트청소": [
        "아파트 입주 전 전체", "아파트 이사 전 전체", "아파트 거주 중 전체",
        "아파트 베란다", "아파트 창틀", "아파트 주방 후드",
        "아파트 욕실 물때", "아파트 실외기실", "아파트 드레스룸",
        "아파트 다용도실",
    ],
    "빌라청소": [
        "빌라 입주 전", "빌라 이사 전", "빌라 계단 포함", "빌라 창틀 먼지",
        "빌라 베란다 곰팡이", "빌라 주방 기름때", "빌라 욕실 물때",
        "빌라 반지하 습기", "빌라 옥탑방", "빌라 공실 전체",
    ],
    "오피스텔청소": [
        "오피스텔 입주 전", "오피스텔 퇴실 전", "오피스텔 주방 기름때",
        "오피스텔 욕실 물때", "오피스텔 창틀", "오피스텔 붙박이장",
        "오피스텔 옵션 가전", "오피스텔 담배 냄새", "오피스텔 공실",
        "오피스텔 복층",
    ],
    "상가청소": [
        "상가 오픈 전", "상가 폐업 후", "상가 리모델링 후", "상가 바닥 찌든때",
        "상가 유리창", "상가 화장실", "상가 주방 기름때", "상가 간판 먼지",
        "상가 천장 분진", "상가 폐기물 정리 후",
    ],
    "사무실청소": [
        "사무실 입주 전", "사무실 이전 후", "사무실 바닥 왁스",
        "사무실 카펫 먼지", "사무실 유리 파티션", "사무실 책상 먼지",
        "사무실 탕비실", "사무실 화장실", "사무실 정기관리",
        "사무실 폐기물 정리 후",
    ],
    "준공청소": [
        "신축 건물 준공 후", "리모델링 공사 후", "상가 인테리어 후",
        "사무실 인테리어 후", "아파트 공사 분진", "빌라 공사 분진",
        "유리창 보양지 제거", "바닥 시멘트가루", "벽면 분진",
        "준공 검사 전",
    ],
    "폐기물청소": [
        "원룸 폐기물 정리", "투룸 폐기물 정리", "아파트 이사 폐기물",
        "빌라 방치 폐기물", "상가 폐업 폐기물", "사무실 이전 폐기물",
        "가구 철거 후 폐기물", "생활폐기물 정리", "공실 폐기물",
        "창고 폐기물 정리",
    ],
}


SIZE_TARGETS: Sequence[str] = [
    "원룸", "투룸", "쓰리룸", "10평", "15평", "18평", "20평", "24평",
    "25평", "30평", "32평", "34평", "40평", "45평", "50평",
]

SIZE_SERVICES: Sequence[str] = [
    "입주청소", "이사청소", "거주청소", "원룸청소",
    "아파트청소", "빌라청소", "오피스텔청소",
]

PRICE_INTENTS: Sequence[str] = ["비용", "가격", "견적", "청소시간"]


PROBLEMS_BY_SERVICE: Dict[str, Sequence[str]] = {
    "입주청소": [
        "창틀 시멘트가루 제거", "바닥 공사 분진 제거", "욕실 백시멘트 제거",
        "주방 수납장 톱밥 먼지 제거", "베란다 탄성코트 분진 제거",
        "유리창 스티커 자국 제거",
    ],
    "이사청소": [
        "주방 후드 기름때 제거", "화장실 물때 제거", "창틀 묵은먼지 제거",
        "베란다 곰팡이 제거", "붙박이장 먼지 제거", "배수구 악취 제거",
    ],
    "거주청소": [
        "주방 찌든 기름때 제거", "욕실 석회 물때 제거", "창틀 검은먼지 제거",
        "베란다 결로 곰팡이 제거", "반려동물 털 제거", "담배 니코틴 오염 제거",
    ],
    "원룸청소": [
        "담배 냄새와 니코틴 제거", "화장실 곰팡이 제거", "주방 기름때 제거",
        "냉장고 악취 제거", "옵션 세탁기 자리 청소", "퇴실 폐기물 정리",
    ],
    "아파트청소": [
        "실외기실 비둘기 배설물 청소", "베란다 곰팡이 제거",
        "창틀 미세먼지 제거", "주방 후드 기름때 제거",
        "욕실 석회 제거", "다용도실 배수구 세척",
    ],
    "빌라청소": [
        "반지하 곰팡이 제거", "창틀 묵은먼지 제거", "베란다 물때 제거",
        "주방 기름때 제거", "욕실 실리콘 곰팡이 제거", "계단 먼지 제거",
    ],
    "오피스텔청소": [
        "옵션 냉장고 악취 제거", "인덕션 기름때 제거", "욕실 물때 제거",
        "창틀 먼지 제거", "붙박이장 먼지 제거", "담배 냄새 제거",
    ],
    "상가청소": [
        "바닥 기름때 제거", "유리창 스티커 자국 제거", "화장실 물때 제거",
        "주방 후드 기름때 제거", "인테리어 분진 제거", "폐업 폐기물 정리",
    ],
    "사무실청소": [
        "카펫 먼지 제거", "유리 파티션 손자국 제거", "바닥 왁스 작업",
        "탕비실 기름때 제거", "화장실 물때 제거", "책상과 전산기기 먼지 제거",
    ],
    "준공청소": [
        "시멘트가루 제거", "실리콘 자국 제거", "페인트 자국 제거",
        "보양지 제거", "유리창 스티커 제거", "공사 분진 제거",
    ],
    "폐기물청소": [
        "생활폐기물 분리 정리", "방치 가구 처리", "이사 후 폐기물 정리",
        "폐업 집기 정리", "공실 쓰레기 정리", "창고 적치물 정리",
    ],
}


CLASSIC_MODIFIERS: Sequence[str] = [
    "전문업체", "잘하는곳", "추천", "가격", "비용", "견적",
]


EN_REGION = {
    "서울": "seoul",
    "인천": "incheon",
    "경기": "gyeonggi",
}

EN_SERVICE = {
    "입주청소": "move-in-cleaning",
    "이사청소": "move-out-cleaning",
    "거주청소": "occupied-home-cleaning",
    "원룸청소": "studio-cleaning",
    "아파트청소": "apartment-cleaning",
    "빌라청소": "villa-cleaning",
    "오피스텔청소": "officetel-cleaning",
    "상가청소": "store-cleaning",
    "사무실청소": "office-cleaning",
    "준공청소": "post-construction-cleaning",
    "폐기물청소": "waste-cleaning",
}

SLUG_PHRASES = {
    "신축": "new", "아파트": "apartment", "입주 전": "before-move-in",
    "이사 전": "before-moving", "이사 후": "after-moving",
    "퇴실 전": "before-move-out", "공실": "vacant", "원룸": "studio",
    "투룸": "two-room", "쓰리룸": "three-room", "창틀": "window-track",
    "먼지": "dust", "미세먼지": "fine-dust", "묵은먼지": "old-dust",
    "주방": "kitchen", "수납장": "cabinet", "후드": "hood",
    "기름때": "grease", "화장실": "bathroom", "욕실": "bathroom",
    "물때": "water-stain", "석회": "limescale", "곰팡이": "mold",
    "베란다": "balcony", "실외기실": "outdoor-unit-room",
    "비둘기 배설물": "pigeon-droppings", "드레스룸": "dressing-room",
    "붙박이장": "built-in-closet", "다용도실": "utility-room",
    "배수구": "drain", "악취": "odor", "담배": "tobacco",
    "니코틴": "nicotine", "시멘트가루": "cement-dust",
    "공사 분진": "construction-dust", "분진": "dust",
    "탄성코트": "elastic-coat", "사무실": "office", "상가": "store",
    "바닥": "floor", "왁스": "wax", "유리창": "window",
    "유리 파티션": "glass-partition", "카펫": "carpet",
    "폐기물": "waste", "정리": "cleanup", "제거": "removal",
    "청소": "cleaning", "전문업체": "company", "잘하는곳": "best",
    "추천": "recommended", "가격": "price", "비용": "cost",
    "견적": "quote", "청소시간": "cleaning-time",
}


@dataclass
class KeywordRow:
    keyword: str
    slug: str
    region: str
    service: str
    category: str
    title: str
    description: str
    h1: str
    intent: str = ""
    topic: str = ""


def safe_token(text: str) -> str:
    text = text.lower().strip()
    for korean, english in sorted(SLUG_PHRASES.items(), key=lambda x: len(x[0]), reverse=True):
        text = text.replace(korean, f" {english} ")
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def romanize_region(text: str) -> str:
    replacements = {
        "강남구": "gangnam-gu", "서초구": "seocho-gu", "송파구": "songpa-gu",
        "강동구": "gangdong-gu", "마포구": "mapo-gu", "용산구": "yongsan-gu",
        "성동구": "seongdong-gu", "광진구": "gwangjin-gu", "동작구": "dongjak-gu",
        "관악구": "gwanak-gu", "영등포구": "yeongdeungpo-gu", "구로구": "guro-gu",
        "금천구": "geumcheon-gu", "양천구": "yangcheon-gu", "강서구": "gangseo-gu",
        "은평구": "eunpyeong-gu", "서대문구": "seodaemun-gu", "종로구": "jongno-gu",
        "중구": "jung-gu", "동대문구": "dongdaemun-gu", "중랑구": "jungnang-gu",
        "성북구": "seongbuk-gu", "강북구": "gangbuk-gu", "도봉구": "dobong-gu",
        "노원구": "nowon-gu", "미추홀구": "michuhol-gu", "연수구": "yeonsu-gu",
        "남동구": "namdong-gu", "부평구": "bupyeong-gu", "계양구": "gyeyang-gu",
        "서구": "seo-gu", "동구": "dong-gu", "강화군": "ganghwa-gun",
        "수원시": "suwon-si", "성남시": "seongnam-si", "용인시": "yongin-si",
        "고양시": "goyang-si", "부천시": "bucheon-si", "안산시": "ansan-si",
        "안양시": "anyang-si", "남양주시": "namyangju-si", "화성시": "hwaseong-si",
        "평택시": "pyeongtaek-si", "의정부시": "uijeongbu-si", "시흥시": "siheung-si",
        "파주시": "paju-si", "김포시": "gimpo-si", "광명시": "gwangmyeong-si",
        "광주시": "gwangju-si", "군포시": "gunpo-si", "하남시": "hanam-si",
        "오산시": "osan-si", "이천시": "icheon-si", "안성시": "anseong-si",
        "의왕시": "uiwang-si", "양주시": "yangju-si", "구리시": "guri-si",
        "포천시": "pocheon-si", "여주시": "yeoju-si", "동두천시": "dongducheon-si",
        "과천시": "gwacheon-si", "김포": "gimpo", "부천": "bucheon",
        "고양": "goyang", "일산": "ilsan",
    }
    return replacements.get(text, safe_token(text))


def stable_suffix(text: str, length: int = 8) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def make_slug(region1: str, region2: str, service: str, topic: str, intent: str) -> str:
    topic_token = safe_token(topic)
    parts = [
        EN_REGION.get(region1, safe_token(region1)),
        romanize_region(region2),
        EN_SERVICE.get(service, safe_token(service)),
        topic_token,
    ]
    slug = "-".join(part for part in parts if part)
    slug = re.sub(r"-{2,}", "-", slug).strip("-").lower()

    if not topic_token:
        slug = f"{slug}-{stable_suffix(topic)}"
    if intent == "classic":
        slug = f"{slug}-service"
    return slug


def make_description(keyword: str, service: str, intent: str, topic: str) -> str:
    if intent == "situation":
        text = (
            f"{keyword} 작업 범위와 청소 순서를 안내합니다. "
            f"{topic} 현장의 오염 상태를 확인하고 필요한 {service} 항목을 상담합니다."
        )
    elif intent == "size":
        text = (
            f"{keyword} 정보를 확인하세요. 평형과 구조, 오염도에 따른 작업 범위와 "
            f"예상 시간, 현장별 {service} 견적 기준을 안내합니다."
        )
    elif intent == "problem":
        text = (
            f"{keyword}가 필요한 현장을 위한 안내입니다. 오염 원인과 마감재 상태를 확인한 뒤 "
            f"손상을 줄이는 방식으로 {service} 범위를 상담합니다."
        )
    else:
        text = (
            f"{keyword} 상담이 필요하신 분을 위한 안내입니다. "
            f"현장 구조와 오염도에 맞춰 {service} 작업 범위와 견적을 안내합니다."
        )
    return text[:155]


def make_row(
    region1: str,
    region2: str,
    service: str,
    topic: str,
    intent: str,
    keyword: str,
) -> KeywordRow:
    region = f"{region1} {region2}".strip()
    return KeywordRow(
        keyword=keyword,
        slug=make_slug(region1, region2, service, topic, intent),
        region=region,
        service=service,
        category=service,
        title=f"{keyword} | {BRAND_NAME}",
        description=make_description(keyword, service, intent, topic),
        h1=keyword,
        intent=intent,
        topic=topic,
    )


def generate_situation_candidates() -> List[KeywordRow]:
    rows: List[KeywordRow] = []
    for region1, region2 in REGIONS:
        region = f"{region1} {region2}"
        for service, situations in SERVICE_SITUATIONS.items():
            for situation in situations:
                keyword = f"{region} {situation} {service}"
                rows.append(make_row(region1, region2, service, situation, "situation", keyword))
    return rows


def generate_size_candidates() -> List[KeywordRow]:
    rows: List[KeywordRow] = []
    for region1, region2 in REGIONS:
        region = f"{region1} {region2}"
        for service in SIZE_SERVICES:
            for size in SIZE_TARGETS:
                for price_intent in PRICE_INTENTS:
                    topic = f"{size} {price_intent}"
                    keyword = f"{region} {size} {service} {price_intent}"
                    rows.append(make_row(region1, region2, service, topic, "size", keyword))
    return rows


def generate_problem_candidates() -> List[KeywordRow]:
    rows: List[KeywordRow] = []
    for region1, region2 in REGIONS:
        region = f"{region1} {region2}"
        for service, problems in PROBLEMS_BY_SERVICE.items():
            for problem in problems:
                keyword = f"{region} {problem} {service}"
                rows.append(make_row(region1, region2, service, problem, "problem", keyword))
    return rows


def generate_classic_candidates() -> List[KeywordRow]:
    rows: List[KeywordRow] = []
    for region1, region2 in REGIONS:
        region = f"{region1} {region2}"
        for service in SERVICES:
            for modifier in CLASSIC_MODIFIERS:
                keyword = f"{region} {service} {modifier}"
                rows.append(make_row(region1, region2, service, modifier, "classic", keyword))
    return rows


def unique_rows(rows: Iterable[KeywordRow]) -> List[KeywordRow]:
    result: List[KeywordRow] = []
    seen_keywords: Set[str] = set()
    seen_slugs: Set[str] = set()

    for row in rows:
        if row.keyword in seen_keywords or row.slug in seen_slugs:
            continue
        seen_keywords.add(row.keyword)
        seen_slugs.add(row.slug)
        result.append(row)
    return result


def proportional_quotas(limit: int) -> Dict[str, int]:
    situation = round(limit * 0.50)
    size = round(limit * 0.25)
    problem = round(limit * 0.15)
    classic = limit - situation - size - problem
    return {
        "situation": situation,
        "size": size,
        "problem": problem,
        "classic": classic,
    }


def balanced_pick(
    candidates: Sequence[KeywordRow],
    count: int,
    rng: random.Random,
) -> List[KeywordRow]:
    if count <= 0:
        return []

    shuffled = list(candidates)
    rng.shuffle(shuffled)

    buckets: Dict[Tuple[str, str], List[KeywordRow]] = {}
    for row in shuffled:
        buckets.setdefault((row.region, row.service), []).append(row)

    keys = list(buckets.keys())
    rng.shuffle(keys)

    selected: List[KeywordRow] = []
    while keys and len(selected) < count:
        next_keys: List[Tuple[str, str]] = []
        for key in keys:
            bucket = buckets[key]
            if bucket:
                selected.append(bucket.pop())
                if len(selected) >= count:
                    break
            if bucket:
                next_keys.append(key)
        keys = next_keys

    return selected


def build_rows(limit: int = DEFAULT_LIMIT, seed: int = DEFAULT_SEED) -> List[KeywordRow]:
    if limit <= 0:
        raise ValueError("--limit는 1 이상이어야 합니다.")

    rng = random.Random(seed)
    quotas = proportional_quotas(limit)

    groups = {
        "situation": unique_rows(generate_situation_candidates()),
        "size": unique_rows(generate_size_candidates()),
        "problem": unique_rows(generate_problem_candidates()),
        "classic": unique_rows(generate_classic_candidates()),
    }

    selected: List[KeywordRow] = []
    for group_name in ("situation", "size", "problem", "classic"):
        selected.extend(balanced_pick(groups[group_name], quotas[group_name], rng))

    selected = unique_rows(selected)

    if len(selected) < limit:
        selected_keywords = {row.keyword for row in selected}
        all_candidates: List[KeywordRow] = []
        for group_rows in groups.values():
            all_candidates.extend(group_rows)
        rng.shuffle(all_candidates)

        for row in all_candidates:
            if row.keyword in selected_keywords:
                continue
            selected.append(row)
            selected_keywords.add(row.keyword)
            if len(selected) >= limit:
                break

    if len(selected) < limit:
        raise RuntimeError(
            f"요청한 {limit}개를 만들 후보가 부족합니다. 생성 가능 수: {len(selected)}"
        )

    rng.shuffle(selected)
    return selected[:limit]


def read_existing(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        if FALLBACK_CSV.exists():
            path = FALLBACK_CSV
        else:
            return []

    if path.suffix.lower() in {".xlsx", ".xls"}:
        if pd is None:
            raise ImportError(
                "엑셀 읽기에는 pandas/openpyxl이 필요합니다. "
                "pip install pandas openpyxl"
            )
        df = pd.read_excel(path)
        return df.fillna("").to_dict(orient="records")

    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    raise ValueError("지원하는 출력 형식은 .xlsx, .xls, .csv입니다.")


def dedupe_rows(
    existing: List[Dict[str, str]],
    new_rows: List[KeywordRow],
    append: bool,
) -> List[Dict[str, str]]:
    final: List[Dict[str, str]] = []
    seen_keywords: Set[str] = set()
    seen_slugs: Set[str] = set()

    if append:
        for row in existing:
            keyword = str(row.get("keyword", "")).strip()
            slug = str(row.get("slug", "")).strip()
            if not keyword or not slug:
                continue
            if keyword in seen_keywords or slug in seen_slugs:
                continue
            seen_keywords.add(keyword)
            seen_slugs.add(slug)
            final.append(row)

    for row in new_rows:
        data = asdict(row)
        if data["keyword"] in seen_keywords or data["slug"] in seen_slugs:
            continue
        seen_keywords.add(data["keyword"])
        seen_slugs.add(data["slug"])
        final.append(data)

    return final


def save_rows(rows: List[Dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "keyword", "slug", "region", "service", "category",
        "title", "description", "h1", "intent", "topic",
    ]

    if output.suffix.lower() in {".xlsx", ".xls"}:
        if pd is None:
            raise ImportError(
                "엑셀 저장에는 pandas/openpyxl이 필요합니다. "
                "pip install pandas openpyxl"
            )
        df = pd.DataFrame(rows)
        for column in columns:
            if column not in df.columns:
                df[column] = ""
        df = df[columns]
        df.to_excel(output, index=False)
        return

    if output.suffix.lower() == ".csv":
        with open(output, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})
        return

    raise ValueError("지원하는 출력 형식은 .xlsx, .xls, .csv입니다.")


def print_summary(rows: Sequence[Dict[str, str]], added_count: int, output: Path) -> None:
    intent_counts: Dict[str, int] = {}
    for row in rows:
        intent = str(row.get("intent", "")).strip() or "기존"
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("=" * 62)
    print(f"저장 완료: {output}")
    print(f"이번 생성 후보 반영 수: {added_count}")
    print(f"최종 전체 키워드 수: {len(rows)}")
    print("-" * 62)
    for name in ("situation", "size", "problem", "classic", "기존"):
        if name in intent_counts:
            print(f"{name:>10}: {intent_counts[name]}")
    print("=" * 62)


def generate_keywords(
    output: str = "keywords.xlsx",
    append: bool = True,
    limit: int = DEFAULT_LIMIT,
    seed: int = DEFAULT_SEED,
) -> Path:
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    existing = read_existing(output_path) if append else []
    new_rows = build_rows(limit=limit, seed=seed)
    final = dedupe_rows(existing, new_rows, append=append)
    added_count = len(final) - len(existing)

    save_rows(final, output_path)
    print_summary(final, added_count, output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="V6.1 롱테일 SEO 키워드 생성 엔진"
    )
    parser.add_argument(
        "--output",
        default="keywords.xlsx",
        help="저장 파일명(.xlsx 또는 .csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"새로 생성할 키워드 수(기본 {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="같은 결과를 재현하기 위한 난수 시드",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--append",
        action="store_true",
        help="기존 keywords 파일에 중복 없이 추가",
    )
    mode.add_argument(
        "--replace",
        action="store_true",
        help="기존 파일을 새 키워드로 교체",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    append = not args.replace

    generate_keywords(
        output=args.output,
        append=append,
        limit=args.limit,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
