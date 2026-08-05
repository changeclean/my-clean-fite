#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V9 SEO Incremental Engine
============================

현재 5월 말 정상 사이트 구조(루트 index.html + 약 3,000개 폴더)에
신규 롱테일 페이지 3,000개만 안전하게 추가합니다.

핵심 안전장치
-------------
1. 루트 index.html 절대 수정 금지
2. 기존 페이지 폴더 절대 덮어쓰기 금지
3. 실행 전/후 루트 index.html SHA-256 비교
4. 기존 HTML title, 기존 폴더 slug와 중복 제거
5. 실제 루트 폴더 전체를 스캔해 sitemap.xml 갱신
6. Git 현재 브랜치를 자동 감지하여 push
7. --no-git 테스트 지원

기본 실행
---------
python V9.py

10개 테스트
-----------
python V9.py --count 10 --no-git
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = BASE_DIR / "v9_page_template.html"

SITE_URL = "https://clever-griffin-93819d.netlify.app"
BRAND_NAME = "체인지클린"
PHONE = "1688-6751"
DEFAULT_COUNT = 3000
MAX_URLS_PER_SITEMAP = 45000
RSS_MAX_ITEMS = 100
PAGINATION_RADIUS = 5

KEYWORD_CSV = BASE_DIR / "v9_keywords_added.csv"
REPORT_CSV = BASE_DIR / "v9_run_report.csv"
SUMMARY_JSON = BASE_DIR / "v9_run_summary.json"


@dataclass(frozen=True)
class Location:
    keyword: str
    slug: str


@dataclass(frozen=True)
class Candidate:
    keyword: str
    slug: str
    location: str
    service: str
    property_type: str
    intent: str

    @property
    def folder(self) -> Path:
        return BASE_DIR / self.slug

    @property
    def page_path(self) -> Path:
        return self.folder / "index.html"

    @property
    def url(self) -> str:
        return f"{SITE_URL.rstrip('/')}/{self.slug}/"


def log(message: str = "") -> None:
    print(message, flush=True)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def pick(seed: str, items: Sequence[str]) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


LOCATIONS = [
    # 인천
    Location("인천 중구", "incheon-jung-gu"),
    Location("인천 동구", "incheon-dong-gu"),
    Location("인천 미추홀구", "incheon-michuhol-gu"),
    Location("인천 연수구", "incheon-yeonsu-gu"),
    Location("인천 남동구", "incheon-namdong-gu"),
    Location("인천 부평구", "incheon-bupyeong-gu"),
    Location("인천 계양구", "incheon-gyeyang-gu"),
    Location("인천 서구", "incheon-seo-gu"),
    Location("인천 송도동", "incheon-songdo-dong"),
    Location("인천 청라동", "incheon-cheongna-dong"),
    Location("인천 검단동", "incheon-geomdan-dong"),
    Location("인천 주안동", "incheon-juan-dong"),
    Location("인천 구월동", "incheon-guwol-dong"),
    Location("인천 논현동", "incheon-nonhyeon-dong"),
    Location("인천 계산동", "incheon-gyesan-dong"),
    Location("인천 삼산동", "incheon-samsan-dong"),
    Location("인천 부평동", "incheon-bupyeong-dong"),
    Location("인천 간석동", "incheon-ganseok-dong"),
    Location("인천 만수동", "incheon-mansu-dong"),
    Location("인천 당하동", "incheon-dangha-dong"),

    # 김포/부천/고양/일산
    Location("김포 장기동", "gimpo-janggi-dong"),
    Location("김포 구래동", "gimpo-gurae-dong"),
    Location("김포 운양동", "gimpo-unyang-dong"),
    Location("김포 풍무동", "gimpo-pungmu-dong"),
    Location("김포 사우동", "gimpo-sau-dong"),
    Location("김포 마산동", "gimpo-masan-dong"),
    Location("김포 고촌읍", "gimpo-gochon-eup"),
    Location("김포 통진읍", "gimpo-tongjin-eup"),
    Location("부천 중동", "bucheon-jung-dong"),
    Location("부천 상동", "bucheon-sang-dong"),
    Location("부천 송내동", "bucheon-songnae-dong"),
    Location("부천 심곡동", "bucheon-simgok-dong"),
    Location("부천 원종동", "bucheon-wonjong-dong"),
    Location("부천 소사본동", "bucheon-sosabon-dong"),
    Location("부천 옥길동", "bucheon-okgil-dong"),
    Location("고양 화정동", "goyang-hwajeong-dong"),
    Location("고양 행신동", "goyang-haengsin-dong"),
    Location("고양 원흥동", "goyang-wonheung-dong"),
    Location("고양 삼송동", "goyang-samsong-dong"),
    Location("고양 향동동", "goyang-hyangdong-dong"),
    Location("고양 지축동", "goyang-jichuk-dong"),
    Location("일산 백석동", "ilsan-baekseok-dong"),
    Location("일산 마두동", "ilsan-madu-dong"),
    Location("일산 주엽동", "ilsan-juyeop-dong"),
    Location("일산 대화동", "ilsan-daehwa-dong"),
    Location("일산 식사동", "ilsan-siksa-dong"),
    Location("일산 탄현동", "ilsan-tanhyeon-dong"),

    # 서울 주요 구/동
    Location("서울 강남구", "seoul-gangnam-gu"),
    Location("서울 서초구", "seoul-seocho-gu"),
    Location("서울 송파구", "seoul-songpa-gu"),
    Location("서울 강동구", "seoul-gangdong-gu"),
    Location("서울 마포구", "seoul-mapo-gu"),
    Location("서울 용산구", "seoul-yongsan-gu"),
    Location("서울 성동구", "seoul-seongdong-gu"),
    Location("서울 광진구", "seoul-gwangjin-gu"),
    Location("서울 영등포구", "seoul-yeongdeungpo-gu"),
    Location("서울 구로구", "seoul-guro-gu"),
    Location("서울 금천구", "seoul-geumcheon-gu"),
    Location("서울 양천구", "seoul-yangcheon-gu"),
    Location("서울 강서구", "seoul-gangseo-gu"),
    Location("서울 은평구", "seoul-eunpyeong-gu"),
    Location("서울 서대문구", "seoul-seodaemun-gu"),
    Location("서울 동작구", "seoul-dongjak-gu"),
    Location("서울 관악구", "seoul-gwanak-gu"),
    Location("서울 동대문구", "seoul-dongdaemun-gu"),
    Location("서울 중랑구", "seoul-jungnang-gu"),
    Location("서울 노원구", "seoul-nowon-gu"),
    Location("서울 도봉구", "seoul-dobong-gu"),
    Location("서울 강북구", "seoul-gangbuk-gu"),
    Location("서울 성북구", "seoul-seongbuk-gu"),
    Location("서울 종로구", "seoul-jongno-gu"),
    Location("서울 중구", "seoul-jung-gu"),
    Location("서울 잠실동", "seoul-jamsil-dong"),
    Location("서울 역삼동", "seoul-yeoksam-dong"),
    Location("서울 마곡동", "seoul-magok-dong"),
    Location("서울 문정동", "seoul-munjeong-dong"),

    # 경기 주요 지역
    Location("파주 운정동", "paju-unjeong-dong"),
    Location("파주 야당동", "paju-yadang-dong"),
    Location("시흥 배곧동", "siheung-baegot-dong"),
    Location("시흥 정왕동", "siheung-jeongwang-dong"),
    Location("광명 철산동", "gwangmyeong-cheolsan-dong"),
    Location("광명 일직동", "gwangmyeong-iljik-dong"),
    Location("안양 평촌동", "anyang-pyeongchon-dong"),
    Location("안양 호계동", "anyang-hogye-dong"),
    Location("군포 산본동", "gunpo-sanbon-dong"),
    Location("의왕 포일동", "uiwang-poil-dong"),
    Location("수원 광교동", "suwon-gwanggyo-dong"),
    Location("수원 영통동", "suwon-yeongtong-dong"),
    Location("성남 분당구", "seongnam-bundang-gu"),
    Location("성남 판교동", "seongnam-pangyo-dong"),
    Location("용인 수지구", "yongin-suji-gu"),
    Location("용인 기흥구", "yongin-giheung-gu"),
    Location("하남 미사동", "hanam-misa-dong"),
    Location("남양주 다산동", "namyangju-dasan-dong"),
    Location("남양주 별내동", "namyangju-byeollae-dong"),
    Location("의정부 민락동", "uijeongbu-millak-dong"),
    Location("양주 옥정동", "yangju-okjeong-dong"),
    Location("구리 갈매동", "guri-galmae-dong"),
]

# 사용자가 요청한 핵심 서비스 중심
SERVICES = [
    ("입주청소", "move-in-cleaning", 35),
    ("이사청소", "moving-cleaning", 25),
    ("거주청소", "residential-cleaning", 10),
    ("상가청소", "store-cleaning", 8),
    ("사무실청소", "office-cleaning", 8),
    ("원룸청소", "one-room-cleaning", 5),
    ("빌라청소", "villa-cleaning", 3),
    ("오피스텔청소", "officetel-cleaning", 3),
    ("폐기물청소", "waste-cleaning", 3),
]

PROPERTY_TYPES = [
    ("아파트", "apartment"),
    ("원룸", "one-room"),
    ("빌라", "villa"),
    ("오피스텔", "officetel"),
    ("상가", "store"),
    ("사무실", "office"),
]

INTENTS = [
    ("전문업체", "company"),
    ("비용", "cost"),
    ("가격", "price"),
    ("견적", "estimate"),
    ("예약", "booking"),
    ("추천", "recommend"),
    ("후기", "review"),
    ("잘하는곳", "best"),
    ("업체", "service"),
    ("당일상담", "same-day-consult"),
    ("주말예약", "weekend-booking"),
    ("청소범위", "scope"),
]

SITUATIONS = [
    ("입주 전", "before-move-in"),
    ("이사 전", "before-moving"),
    ("이사 후", "after-moving"),
    ("공실", "empty-house"),
    ("주말", "weekend"),
    ("급한 일정", "urgent"),
]


def normalize_keyword(value: str) -> str:
    return re.sub(r"[\s·ㆍ,./_-]+", "", value).casefold()


def existing_state() -> tuple[set[str], set[str], list[str]]:
    """
    고속 기존 상태 스캔.

    기존 버전은 약 3천 개 index.html 내용을 모두 열어 title/H1을 읽어서
    Windows에서 매우 오래 걸릴 수 있었습니다.

    이 버전은:
    - 기존 폴더명(slug)만 빠르게 수집
    - 과거 V8 생성 기록 CSV가 있으면 키워드 중복 방지에 활용
    - 기존 HTML 파일 내용은 읽지 않음
    """
    existing_slugs: set[str] = set()
    existing_keywords: set[str] = set()
    existing_urls: list[str] = []

    ignored = {
        ".git", ".github", "images", "사이트 이름",
        "__pycache__", "node_modules",
    }

    scanned = 0
    for child in BASE_DIR.iterdir():
        if not child.is_dir() or child.name in ignored or child.name.startswith("."):
            continue

        page = child / "index.html"
        if not page.exists():
            continue

        existing_slugs.add(child.name.casefold())
        existing_urls.append(f"{SITE_URL.rstrip('/')}/{child.name}/")
        scanned += 1

        if scanned % 500 == 0:
            log(f"기존 폴더 확인: {scanned:,}개")

    # V8이 이전에 만든 키워드는 CSV에서 중복 방지
    if KEYWORD_CSV.exists():
        with KEYWORD_CSV.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                keyword = clean(row.get("keyword"))
                slug = clean(row.get("slug"))

                if keyword:
                    existing_keywords.add(normalize_keyword(keyword))
                if slug:
                    existing_slugs.add(slug.casefold())

    return existing_slugs, existing_keywords, sorted(set(existing_urls))


def weighted_services() -> list[tuple[str, str]]:
    expanded: list[tuple[str, str]] = []
    for keyword, slug, weight in SERVICES:
        expanded.extend([(keyword, slug)] * weight)
    return expanded


def candidate_stream() -> Iterable[Candidate]:
    services = weighted_services()

    # 1차: 지역 + 공간 + 서비스 + 상업 의도
    for location in LOCATIONS:
        for service_keyword, service_slug in services:
            for property_keyword, property_slug in PROPERTY_TYPES:
                for intent_keyword, intent_slug in INTENTS:
                    # 어색한 중복을 줄이기 위한 정리
                    if service_keyword in ("원룸청소", "빌라청소", "오피스텔청소", "아파트청소"):
                        if property_keyword not in service_keyword:
                            continue
                        keyword = f"{location.keyword} {service_keyword} {intent_keyword}"
                        slug = f"seo-{location.slug}-{service_slug}-{intent_slug}"
                    elif service_keyword == "상가청소":
                        if property_keyword != "상가":
                            continue
                        keyword = f"{location.keyword} 상가청소 {intent_keyword}"
                        slug = f"seo-{location.slug}-store-cleaning-{intent_slug}"
                    elif service_keyword == "사무실청소":
                        if property_keyword != "사무실":
                            continue
                        keyword = f"{location.keyword} 사무실청소 {intent_keyword}"
                        slug = f"seo-{location.slug}-office-cleaning-{intent_slug}"
                    elif service_keyword == "폐기물청소":
                        if property_keyword not in ("원룸", "빌라", "오피스텔", "상가", "사무실"):
                            continue
                        keyword = f"{location.keyword} {property_keyword} 폐기물청소 {intent_keyword}"
                        slug = f"seo-{location.slug}-{property_slug}-waste-cleaning-{intent_slug}"
                    else:
                        keyword = f"{location.keyword} {property_keyword} {service_keyword} {intent_keyword}"
                        slug = f"seo-{location.slug}-{property_slug}-{service_slug}-{intent_slug}"

                    yield Candidate(
                        keyword=keyword,
                        slug=slug,
                        location=location.keyword,
                        service=service_keyword,
                        property_type=property_keyword,
                        intent=intent_keyword,
                    )

    # 2차: 상황형 롱테일
    for location in LOCATIONS:
        for service_keyword, service_slug, _weight in SERVICES:
            if service_keyword not in ("입주청소", "이사청소", "거주청소", "폐기물청소"):
                continue
            for property_keyword, property_slug in PROPERTY_TYPES[:4]:
                for situation_keyword, situation_slug in SITUATIONS:
                    keyword = (
                        f"{location.keyword} {property_keyword} "
                        f"{situation_keyword} {service_keyword}"
                    )
                    slug = (
                        f"seo-{location.slug}-{property_slug}-"
                        f"{situation_slug}-{service_slug}"
                    )
                    yield Candidate(
                        keyword=keyword,
                        slug=slug,
                        location=location.keyword,
                        service=service_keyword,
                        property_type=property_keyword,
                        intent=situation_keyword,
                    )


def select_new_candidates(count: int) -> tuple[list[Candidate], int, int]:
    existing_slugs, existing_keywords, _ = existing_state()
    selected: list[Candidate] = []
    seen_slugs = set(existing_slugs)
    seen_keywords = set(existing_keywords)

    duplicate_slug = 0
    duplicate_keyword = 0

    for candidate in candidate_stream():
        slug_key = candidate.slug.casefold()
        keyword_key = normalize_keyword(candidate.keyword)

        if slug_key in seen_slugs or candidate.folder.exists():
            duplicate_slug += 1
            continue
        if keyword_key in seen_keywords:
            duplicate_keyword += 1
            continue

        seen_slugs.add(slug_key)
        seen_keywords.add(keyword_key)
        selected.append(candidate)

        if len(selected) >= count:
            break

    if len(selected) < count:
        raise RuntimeError(
            f"신규 키워드를 {count:,}개 확보하지 못했습니다. "
            f"확보: {len(selected):,}개"
        )

    return selected, duplicate_slug, duplicate_keyword



def keyword_quality_score(page: Candidate) -> int:
    score = 100
    words = page.keyword.split()

    if len(words) < 4:
        score -= 20
    if len(words) > 9:
        score -= 10
    if page.service not in page.keyword:
        score -= 25
    if page.location not in page.keyword:
        score -= 20
    if page.intent not in page.keyword:
        score -= 10
    if page.keyword.count(page.property_type) > 1:
        score -= 10
    if "청소 청소" in page.keyword:
        score -= 20

    return max(0, min(100, score))


def summarize_keyword_quality(pages: Sequence[Candidate]) -> dict[str, int]:
    buckets = {"A_90_100": 0, "B_80_89": 0, "C_below_80": 0}
    for page in pages:
        score = keyword_quality_score(page)
        if score >= 90:
            buckets["A_90_100"] += 1
        elif score >= 80:
            buckets["B_80_89"] += 1
        else:
            buckets["C_below_80"] += 1
    return buckets

def make_title(page: Candidate) -> str:
    suffix = pick(page.slug + "-title", (
        " | 체인지클린",
        " | 청소 범위와 견적 안내",
        " | 지역 청소업체 안내",
    ))
    max_keyword = max(20, 68 - len(suffix))
    return page.keyword[:max_keyword].rstrip() + suffix


def make_description(page: Candidate) -> str:
    options = (
        f"{page.keyword}를 알아보는 분을 위해 작업 범위, 진행 순서, 비용과 견적 상담 시 확인할 사항을 정리했습니다. 체인지클린 청소 안내입니다.",
        f"{page.location} {page.property_type} {page.service} 관련 가격, 예약, 준비사항과 구역별 작업 범위를 안내합니다. 현장 상태에 맞춰 상담받아보세요.",
        f"{page.keyword} 현장의 청소 범위와 준비사항, 구역별 확인 항목을 안내합니다. 입주·이사·상가·사무실 청소 상담이 가능합니다.",
        f"{page.location}에서 {page.service} 업체를 찾는 분을 위한 안내입니다. 평수, 오염 상태, 짐 유무에 따른 견적 확인사항을 정리했습니다.",
        f"{page.keyword} 예약 전 확인할 작업 범위와 예상 진행 순서, 현장별 추가 확인사항을 안내합니다.",
        f"{page.property_type} {page.service} 비용과 작업 범위가 궁금한 분을 위해 {page.location} 기준 상담 전 체크사항을 정리했습니다.",
    )
    return pick(page.slug + "-description", options)[:165]

def make_feedback(page: Candidate) -> str:
    options = (
        f"{page.location} {page.property_type} 현장을 확인한 뒤 {page.service} 작업 순서를 정했습니다. 창틀과 수납장 안쪽 먼지를 먼저 정리하고 주방과 욕실의 생활 오염을 구역별로 세척했습니다. 마지막에는 바닥과 모서리, 손이 자주 닿는 부분까지 다시 확인했습니다.",
        f"{page.keyword} 상담 후 공간 구조와 오염 상태를 먼저 살폈습니다. 같은 평수라도 짐의 유무와 오염 범위에 따라 필요한 장비와 작업 시간이 달라질 수 있어 공간별로 순서를 나누어 진행했습니다.",
        f"{page.location}에서 진행한 {page.service}는 높은 곳의 먼지 제거부터 시작했습니다. 창틀, 주방, 욕실, 바닥 순서로 작업하고 수납장 내부와 배수구 주변도 잔여 오염이 없는지 마무리 점검했습니다.",
        f"{page.property_type} {page.service} 현장은 입실 일정과 작업 시간을 먼저 확인했습니다. 작업 동선이 겹치지 않도록 구역을 나누고 먼지 제거, 세척, 건조, 검수 순서로 마무리했습니다.",
        f"{page.keyword} 작업에서는 오염도가 높은 주방과 욕실을 분리해 진행했습니다. 세제 잔여물이 남지 않도록 여러 번 닦고, 바닥과 걸레받이까지 확인한 뒤 고객 확인을 진행했습니다.",
        f"{page.location} 현장은 창틀 분진과 수납장 안쪽 먼지가 많아 위쪽부터 아래쪽 순서로 정리했습니다. 마지막에는 전체 환기와 바닥 검수를 진행해 누락 구역을 다시 확인했습니다.",
        f"{page.service}는 눈에 보이는 표면뿐 아니라 손잡이, 문틀, 스위치, 수납장 모서리까지 확인하는 과정이 중요합니다. 이번 현장도 구역별 체크리스트에 따라 마무리했습니다.",
        f"{page.keyword} 의뢰는 일정이 촉박해 작업 전 필요한 범위를 먼저 정리했습니다. 필수 구역을 우선 진행하고, 현장 상태를 확인하면서 추가 작업이 필요한 부분을 안내했습니다.",
    )
    return pick(page.slug + "-feedback", options)

def make_faq(page: Candidate) -> str:
    faq_sets = (
        (
            (f"{page.service} 범위는 어디까지인가요?", "기본 범위는 실내 먼지와 생활 오염 제거입니다. 외창, 심한 특수오염, 폐기물 반출은 현장에 따라 별도 확인합니다."),
            ("견적을 받으려면 무엇을 알려드려야 하나요?", "지역, 공간 종류, 평수, 방과 욕실 개수, 짐과 폐기물 유무, 원하는 날짜를 알려주시면 상담이 빠릅니다."),
            ("주말이나 급한 일정도 가능한가요?", "예약 현황에 따라 가능합니다. 원하는 날짜와 입실 또는 이사 시간을 함께 알려주시면 확인해드립니다."),
        ),
        (
            ("청소 시간은 얼마나 걸리나요?", "면적과 오염 상태, 작업 범위와 인원에 따라 달라집니다. 현장 정보 확인 후 예상 시간을 안내합니다."),
            ("준비해야 할 사항이 있나요?", "귀중품과 개인 물품은 미리 정리하고, 주차와 엘리베이터 사용 가능 여부를 알려주시면 좋습니다."),
            ("작업 후 검수도 가능한가요?", "구역별 작업 완료 후 고객님과 함께 확인하거나 사진으로 작업 결과를 안내할 수 있습니다."),
        ),
        (
            ("가격은 평수만으로 결정되나요?", "평수 외에도 방과 욕실 개수, 오염도, 짐 유무, 추가 작업 여부를 함께 확인합니다."),
            ("외창도 기본 범위인가요?", "안전 문제로 외창은 기본 범위에서 제외되는 경우가 많으며 현장 구조에 따라 별도 상담이 필요합니다."),
            ("예약 변경은 어떻게 하나요?", "일정 변경이 필요한 경우 가능한 빨리 연락해주시면 예약 현황을 확인해 조정해드립니다."),
        ),
    )
    items = pick(page.slug + "-faq", faq_sets)
    return "\\n".join(
        f"<div class='faq-item'><h3>Q: {esc(q)}</h3><p>A: {esc(a)}</p></div>"
        for q, a in items
    )

def make_pagination(all_pages: Sequence[Candidate], index: int) -> str:
    start = max(0, index - PAGINATION_RADIUS)
    end = min(len(all_pages), index + PAGINATION_RADIUS + 1)
    links = []

    for position in range(start, end):
        page = all_pages[position]
        active = "active" if position == index else ""
        links.append(
            f'<a href="../{esc(page.slug)}/" class="{active}">{position + 1}</a>'
        )

    return " ".join(links)



def make_related_links(all_pages: Sequence[Candidate], current: Candidate, max_links: int = 12) -> str:
    scored = []
    for page in all_pages:
        if page.slug == current.slug:
            continue

        score = 0
        if page.location == current.location:
            score += 6
        if page.service == current.service:
            score += 5
        if page.property_type == current.property_type:
            score += 3
        if page.intent == current.intent:
            score += 1

        scored.append((score, page.slug, page))

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = [page for score, _slug, page in scored if score > 0][:max_links]

    if not selected:
        selected = [page for _score, _slug, page in scored[:max_links]]

    return "\\n".join(
        f'<a href="../{esc(page.slug)}/" style="display:block;">{esc(page.keyword)}</a>'
        for page in selected
    )

def load_template() -> str:
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(
            f"v9_page_template.html이 없습니다: {TEMPLATE_FILE}"
        )
    return TEMPLATE_FILE.read_text(encoding="utf-8", errors="replace")


def render_page(
    template: str,
    page: Candidate,
    all_pages: Sequence[Candidate],
    index: int,
) -> str:
    replacements = {
        "{{KEYWORD}}": esc(page.keyword),
        "{{TITLE}}": esc(make_title(page)),
        "{{DESCRIPTION}}": esc(make_description(page)),
        "{{CANONICAL}}": esc(page.url),
        "{{DATE}}": datetime.now().strftime("%Y-%m-%d"),
        "{{FEEDBACK}}": esc(make_feedback(page)),
        "{{FAQ}}": make_faq(page),
        "{{PAGINATION}}": make_pagination(all_pages, index),
        "{{RELATED_LINKS}}": make_related_links(all_pages, page),
    }

    content = template
    for token, value in replacements.items():
        content = content.replace(token, value)

    leftovers = re.findall(r"\{\{\s*[^{}]+\s*\}\}", content)
    if leftovers:
        raise ValueError(
            f"{page.slug}: 남은 템플릿 토큰 {sorted(set(leftovers))}"
        )

    return content


def generate_pages(candidates: Sequence[Candidate]) -> list[Candidate]:
    template = load_template()
    created: list[Candidate] = []

    for index, page in enumerate(candidates):
        if page.folder.exists():
            # 안전상 기존 폴더는 절대 건드리지 않습니다.
            continue

        write_text(page.page_path, render_page(template, page, candidates, index))
        created.append(page)

        if len(created) % 100 == 0 or len(created) == len(candidates):
            log(f"신규 페이지 생성: {len(created):,}/{len(candidates):,}")

    if len(created) != len(candidates):
        raise RuntimeError(
            "생성 도중 기존 폴더 충돌이 발생했습니다. 안전을 위해 중단합니다."
        )

    return created


def append_keyword_log(created: Sequence[Candidate]) -> None:
    file_exists = KEYWORD_CSV.exists()

    with KEYWORD_CSV.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "generated_at", "keyword", "slug", "url",
                "location", "service", "property_type", "intent",
            ],
        )
        if not file_exists:
            writer.writeheader()

        generated_at = datetime.now().isoformat(timespec="seconds")
        for page in created:
            writer.writerow({
                "generated_at": generated_at,
                "keyword": page.keyword,
                "slug": page.slug,
                "url": page.url,
                "location": page.location,
                "service": page.service,
                "property_type": page.property_type,
                "intent": page.intent,
            })


def scan_all_page_urls() -> list[str]:
    urls: list[str] = []
    ignored = {
        ".git", ".github", "images", "사이트 이름",
        "__pycache__", "node_modules",
    }

    for child in BASE_DIR.iterdir():
        if not child.is_dir() or child.name in ignored or child.name.startswith("."):
            continue
        if (child / "index.html").exists():
            urls.append(f"{SITE_URL.rstrip('/')}/{child.name}/")

    return sorted(set(urls))


def xml_urlset(urls: Iterable[str], priority: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    body = []

    for url in urls:
        body.append(
            "  <url>\n"
            f"    <loc>{esc(url)}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(body)
        + "\n</urlset>\n"
    )


def xml_sitemap_index(filenames: Iterable[str]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    body = []

    for filename in filenames:
        body.append(
            "  <sitemap>\n"
            f"    <loc>{esc(SITE_URL.rstrip('/') + '/' + filename)}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "  </sitemap>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(body)
        + "\n</sitemapindex>\n"
    )


def generate_sitemaps() -> tuple[int, int]:
    urls = scan_all_page_urls()

    files = ["sitemap-main.xml"]
    write_text(
        BASE_DIR / "sitemap-main.xml",
        xml_urlset([SITE_URL.rstrip("/") + "/"], "1.0"),
    )

    for start in range(0, len(urls), MAX_URLS_PER_SITEMAP):
        number = start // MAX_URLS_PER_SITEMAP + 1
        filename = f"sitemap-pages-{number}.xml"
        files.append(filename)
        write_text(
            BASE_DIR / filename,
            xml_urlset(urls[start:start + MAX_URLS_PER_SITEMAP], "0.8"),
        )

    current = set(files)
    for old in BASE_DIR.glob("sitemap-pages-*.xml"):
        if old.name not in current:
            old.unlink()

    write_text(BASE_DIR / "sitemap.xml", xml_sitemap_index(files))

    for filename in files:
        ET.parse(BASE_DIR / filename)
    ET.parse(BASE_DIR / "sitemap.xml")

    return len(urls), len(files) + 1


def generate_rss(created: Sequence[Candidate]) -> None:
    now = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    items = []
    for page in list(created)[-RSS_MAX_ITEMS:][::-1]:
        items.append(
            "    <item>\n"
            f"      <title>{esc(page.keyword)}</title>\n"
            f"      <link>{esc(page.url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{esc(page.url)}</guid>\n"
            f"      <description>{esc(make_description(page))}</description>\n"
            f"      <pubDate>{now}</pubDate>\n"
            "    </item>"
        )

    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{esc(BRAND_NAME)}</title>\n"
        f"    <link>{esc(SITE_URL)}</link>\n"
        "    <description>체인지클린 신규 롱테일 청소 정보</description>\n"
        "    <language>ko</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n  </channel>\n"
        "</rss>\n"
    )

    write_text(BASE_DIR / "rss.xml", rss)
    ET.parse(BASE_DIR / "rss.xml")


def ensure_robots() -> None:
    robots = BASE_DIR / "robots.txt"
    if not robots.exists():
        write_text(
            robots,
            "User-agent: *\nAllow: /\n\n"
            f"Sitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n",
        )


def verify_created(created: Sequence[Candidate]) -> tuple[int, int, list[str]]:
    passed = 0
    checked = 0
    issues: list[str] = []

    for page in created:
        content = page.page_path.read_text(
            encoding="utf-8", errors="replace"
        )

        page_issues = []
        if page.keyword not in html.unescape(content):
            page_issues.append("키워드 누락")
        if page.url not in html.unescape(content):
            page_issues.append("canonical 누락")
        if "{{" in content or "}}" in content:
            page_issues.append("템플릿 토큰 잔존")

        required_images = (
            "../images/M2.jpg",
            "../images/M3.jpg",
            "../images/M4.jpg",
            "../images/M6.jpg",
            "../images/M7.jpg",
            "../images/M8.jpg",
            "../images/M9.jpg",
            "../images/M10.jpg",
            "../images/kaka1.jpg",
            "../images/banner.jpg",
            "../images/TEL.jpg",
            "../images/under.jpg",
        )
        for image in required_images:
            if image not in content:
                page_issues.append(f"이미지 누락:{image}")
                break

        if page_issues:
            checked += 1
            issues.append(
                f"{page.slug}: " + " | ".join(page_issues)
            )
        else:
            passed += 1

    return passed, checked, issues


def git_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise RuntimeError(
            "현재 폴더가 Git 저장소가 아니거나 브랜치를 확인하지 못했습니다.\n"
            + (result.stdout or "")
        )

    branch = clean(result.stdout)
    if not branch or branch == "HEAD":
        raise RuntimeError("현재 Git 브랜치를 확인하지 못했습니다.")
    return branch


def run_command(command: Sequence[str], allow_nothing: bool = False) -> int:
    log("$ " + " ".join(command))
    result = subprocess.run(
        list(command),
        cwd=BASE_DIR,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    output = result.stdout or ""
    if output.strip():
        print(output)

    if result.returncode and allow_nothing:
        lowered = output.lower()
        if "nothing to commit" in lowered or "nothing added to commit" in lowered:
            return 0

    return result.returncode


def git_deploy(message: str) -> int:
    branch = git_current_branch()
    commands = (
        (["git", "add", "."], False),
        (["git", "commit", "-m", message], True),
        (["git", "push", "origin", branch], False),
    )

    for command, allow_nothing in commands:
        code = run_command(command, allow_nothing)
        if code:
            return code

    return 0


def save_reports(
    requested: int,
    created: Sequence[Candidate],
    duplicate_slug: int,
    duplicate_keyword: int,
    total_urls: int,
    sitemap_files: int,
    passed: int,
    checked: int,
    issues: Sequence[str],
) -> None:
    with REPORT_CSV.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "generated_at", "site_url", "requested",
            "created_pages", "duplicate_slug_skipped",
            "duplicate_keyword_skipped", "total_sitemap_urls",
            "sitemap_files", "verify_pass", "verify_check",
        ])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            SITE_URL,
            requested,
            len(created),
            duplicate_slug,
            duplicate_keyword,
            total_urls,
            sitemap_files,
            passed,
            checked,
        ])

    SUMMARY_JSON.write_text(
        json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "site_url": SITE_URL,
            "requested": requested,
            "created_pages": len(created),
            "duplicate_slug_skipped": duplicate_slug,
            "duplicate_keyword_skipped": duplicate_keyword,
            "total_sitemap_urls": total_urls,
            "sitemap_files": sitemap_files,
            "verify_pass": passed,
            "verify_check": checked,
            "issues": list(issues),
            "created_slugs": [page.slug for page in created],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="기존 사이트를 보존하고 신규 롱테일 페이지를 증분 생성합니다."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help="신규 생성 수. 기본 3000",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Git commit/push를 하지 않음",
    )
    parser.add_argument(
        "--allow-check",
        action="store_true",
        help="검사 CHECK가 있어도 Git 배포",
    )
    parser.add_argument(
        "--message",
        default="",
        help="Git 커밋 메시지",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count = max(1, args.count)

    home = BASE_DIR / "index.html"
    if not home.exists():
        log("루트 index.html이 없습니다. 정상 원본 폴더에서 실행하세요.")
        return 1

    if not TEMPLATE_FILE.exists():
        log("v9_page_template.html이 없습니다.")
        return 1

    home_hash_before = hashlib.sha256(home.read_bytes()).hexdigest()

    log("=" * 72)
    log("V9 SEO Incremental Engine")
    log(f"작업 폴더: {BASE_DIR}")
    log(f"신규 목표: {count:,}개")
    log("기존 index.html과 기존 페이지 폴더는 수정하지 않습니다.")
    log("=" * 72)

    try:
        existing_slugs, _existing_keywords, existing_urls = existing_state()
        log(f"기존 상세페이지 폴더: {len(existing_urls):,}개")
        log(f"기존 slug 인식: {len(existing_slugs):,}개")

        candidates, duplicate_slug, duplicate_keyword = (
            select_new_candidates(count)
        )
        log(f"신규 키워드 확보: {len(candidates):,}개")
        log(f"기존 slug 중복 제외: {duplicate_slug:,}개")
        log(f"기존 키워드 중복 제외: {duplicate_keyword:,}개")
        quality = summarize_keyword_quality(candidates)
        log(f"키워드 품질 A(90~100): {quality['A_90_100']:,}개")
        log(f"키워드 품질 B(80~89): {quality['B_80_89']:,}개")
        log(f"키워드 품질 C(80 미만): {quality['C_below_80']:,}개")

        created = generate_pages(candidates)
        append_keyword_log(created)

        home_hash_after = hashlib.sha256(home.read_bytes()).hexdigest()
        if home_hash_before != home_hash_after:
            raise RuntimeError(
                "안전 중단: 루트 index.html이 변경되었습니다."
            )

        log("루트 index.html 보존 확인: 정상")

        total_urls, sitemap_files = generate_sitemaps()
        generate_rss(created)
        ensure_robots()

        passed, checked, issues = verify_created(created)

        save_reports(
            requested=count,
            created=created,
            duplicate_slug=duplicate_slug,
            duplicate_keyword=duplicate_keyword,
            total_urls=total_urls,
            sitemap_files=sitemap_files,
            passed=passed,
            checked=checked,
            issues=issues,
        )

        log(f"신규 생성 완료: {len(created):,}개")
        log(f"품질검사 PASS: {passed:,}개")
        log(f"품질검사 CHECK: {checked:,}개")
        log(f"사이트맵 전체 상세 URL: {total_urls:,}개")

        if checked and not args.allow_check:
            log("CHECK가 있어 Git 배포를 중단했습니다.")
            log("v9_run_summary.json 확인 후 --allow-check로 실행하세요.")
            return 3

        if args.no_git:
            log("Git 배포를 건너뛰었습니다.")
        else:
            message = args.message or (
                f"V9 add {len(created)} longtail pages "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            code = git_deploy(message)
            if code:
                log(f"Git 배포 실패: 종료 코드 {code}")
                return code

    except Exception as exc:
        log(f"작업 실패: {exc}")
        return 1

    log("=" * 72)
    log("V9 전체 작업 완료")
    log(f"신규 페이지: {len(created):,}개")
    log(f"사이트맵: {SITE_URL.rstrip('/')}/sitemap.xml")
    log("기존 메인과 기존 상세페이지는 유지되었습니다.")
    log("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
