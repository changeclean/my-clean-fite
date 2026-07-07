# -*- coding: utf-8 -*-
"""
V5-0 : keyword_engine_v5.py

역할
- 서울/경기/인천/김포/부천/고양/일산 주요 지역 키워드 자동 생성
- 서비스 조합 생성
- slug 자동 생성
- 기존 keywords.xlsx/keywords.csv와 중복 제거
- keywords.xlsx 저장

실행:
    python keyword_engine_v5.py

옵션:
    python keyword_engine_v5.py --limit 500
    python keyword_engine_v5.py --append
    python keyword_engine_v5.py --output keywords.xlsx
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set

try:
    import pandas as pd
except ImportError:
    pd = None


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE_DIR / "keywords.xlsx"
FALLBACK_CSV = BASE_DIR / "keywords.csv"

BRAND_NAME = "체인지클린"

# 너무 광범위하게 시작하지 않도록 주요 지역 위주.
# 필요하면 여기에 동/읍/면까지 계속 추가하면 됩니다.
REGIONS = [
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

    # 경기 주요
    ("경기", "수원시"), ("경기", "성남시"), ("경기", "용인시"), ("경기", "고양시"),
    ("경기", "부천시"), ("경기", "안산시"), ("경기", "안양시"), ("경기", "남양주시"),
    ("경기", "화성시"), ("경기", "평택시"), ("경기", "의정부시"), ("경기", "시흥시"),
    ("경기", "파주시"), ("경기", "김포시"), ("경기", "광명시"), ("경기", "광주시"),
    ("경기", "군포시"), ("경기", "하남시"), ("경기", "오산시"), ("경기", "이천시"),
    ("경기", "안성시"), ("경기", "의왕시"), ("경기", "양주시"), ("경기", "구리시"),
    ("경기", "포천시"), ("경기", "여주시"), ("경기", "동두천시"), ("경기", "과천시"),

    # 사용자가 특히 자주 언급한 지역
    ("경기", "김포"), ("경기", "부천"), ("경기", "고양"), ("경기", "일산"),
]

SERVICES = [
    "입주청소",
    "이사청소",
    "준공청소",
    "상가청소",
    "사무실청소",
    "빌라청소",
    "아파트청소",
    "오피스텔청소",
    "거주청소",
]

MODIFIERS = [
    "",
    "전문업체",
    "잘하는곳",
    "가격",
    "비용",
    "견적",
]

EN_REGION = {
    "서울": "seoul",
    "인천": "incheon",
    "경기": "gyeonggi",
}

EN_SERVICE = {
    "입주청소": "move-in-cleaning",
    "이사청소": "move-out-cleaning",
    "준공청소": "post-construction-cleaning",
    "상가청소": "store-cleaning",
    "사무실청소": "office-cleaning",
    "빌라청소": "villa-cleaning",
    "아파트청소": "apartment-cleaning",
    "오피스텔청소": "officetel-cleaning",
    "거주청소": "home-cleaning",
}

EN_MODIFIER = {
    "전문업체": "company",
    "잘하는곳": "best",
    "가격": "price",
    "비용": "cost",
    "견적": "quote",
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


def romanize_simple(text: str) -> str:
    # 완전한 한글 로마자 변환은 아니지만 URL 충돌 방지용으로 안정적인 영문/숫자/한글 slug를 만듭니다.
    text = text.lower().strip()
    replacements = {
        "강남구": "gangnam-gu", "서초구": "seocho-gu", "송파구": "songpa-gu", "강동구": "gangdong-gu",
        "마포구": "mapo-gu", "용산구": "yongsan-gu", "성동구": "seongdong-gu", "광진구": "gwangjin-gu",
        "동작구": "dongjak-gu", "관악구": "gwanak-gu", "영등포구": "yeongdeungpo-gu", "구로구": "guro-gu",
        "금천구": "geumcheon-gu", "양천구": "yangcheon-gu", "강서구": "gangseo-gu", "은평구": "eunpyeong-gu",
        "서대문구": "seodaemun-gu", "종로구": "jongno-gu", "중구": "jung-gu", "동대문구": "dongdaemun-gu",
        "중랑구": "jungnang-gu", "성북구": "seongbuk-gu", "강북구": "gangbuk-gu", "도봉구": "dobong-gu",
        "노원구": "nowon-gu", "미추홀구": "michuhol-gu", "연수구": "yeonsu-gu", "남동구": "namdong-gu",
        "부평구": "bupyeong-gu", "계양구": "gyeyang-gu", "서구": "seo-gu", "동구": "dong-gu",
        "강화군": "ganghwa-gun", "수원시": "suwon-si", "성남시": "seongnam-si", "용인시": "yongin-si",
        "고양시": "goyang-si", "부천시": "bucheon-si", "안산시": "ansan-si", "안양시": "anyang-si",
        "남양주시": "namyangju-si", "화성시": "hwaseong-si", "평택시": "pyeongtaek-si",
        "의정부시": "uijeongbu-si", "시흥시": "siheung-si", "파주시": "paju-si", "김포시": "gimpo-si",
        "광명시": "gwangmyeong-si", "광주시": "gwangju-si", "군포시": "gunpo-si", "하남시": "hanam-si",
        "오산시": "osan-si", "이천시": "icheon-si", "안성시": "anseong-si", "의왕시": "uiwang-si",
        "양주시": "yangju-si", "구리시": "guri-si", "포천시": "pocheon-si", "여주시": "yeoju-si",
        "동두천시": "dongducheon-si", "과천시": "gwacheon-si", "김포": "gimpo", "부천": "bucheon",
        "고양": "goyang", "일산": "ilsan",
    }
    return replacements.get(text, re.sub(r"[^a-z0-9가-힣]+", "-", text).strip("-"))


def make_slug(region1: str, region2: str, service: str, modifier: str = "") -> str:
    parts = [
        EN_REGION.get(region1, romanize_simple(region1)),
        romanize_simple(region2),
        EN_SERVICE.get(service, romanize_simple(service)),
    ]
    if modifier:
        parts.append(EN_MODIFIER.get(modifier, romanize_simple(modifier)))
    slug = "-".join([p for p in parts if p])
    slug = re.sub(r"-{2,}", "-", slug).strip("-").lower()
    return slug


def build_keyword(region1: str, region2: str, service: str, modifier: str) -> str:
    base = f"{region1} {region2} {service}"
    if modifier:
        return f"{base} {modifier}"
    return base


def build_rows() -> List[KeywordRow]:
    rows = []
    seen_slugs: Set[str] = set()

    for region1, region2 in REGIONS:
        region = f"{region1} {region2}".strip()
        for service in SERVICES:
            for modifier in MODIFIERS:
                keyword = build_keyword(region1, region2, service, modifier)
                slug = make_slug(region1, region2, service, modifier)

                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)

                title = f"{keyword} | {BRAND_NAME}"
                description = f"{keyword} 전문업체 {BRAND_NAME}. 현장 상황에 맞춘 입주청소, 이사청소, 상가청소, 사무실청소 상담을 안내합니다."
                h1 = keyword

                rows.append(KeywordRow(
                    keyword=keyword,
                    slug=slug,
                    region=region,
                    service=service,
                    category=service,
                    title=title,
                    description=description[:155],
                    h1=h1,
                ))

    return rows


def read_existing(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        if FALLBACK_CSV.exists():
            path = FALLBACK_CSV
        else:
            return []

    if path.suffix.lower() in [".xlsx", ".xls"]:
        if pd is None:
            return []
        df = pd.read_excel(path)
        return df.fillna("").to_dict(orient="records")

    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    return []


def dedupe_rows(existing: List[Dict[str, str]], new_rows: List[KeywordRow], append: bool) -> List[Dict[str, str]]:
    final: List[Dict[str, str]] = []

    seen_keywords = set()
    seen_slugs = set()

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
        d = asdict(row)
        if d["keyword"] in seen_keywords or d["slug"] in seen_slugs:
            continue
        seen_keywords.add(d["keyword"])
        seen_slugs.add(d["slug"])
        final.append(d)

    return final


def save_rows(rows: List[Dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    columns = ["keyword", "slug", "region", "service", "category", "title", "description", "h1"]

    if output.suffix.lower() in [".xlsx", ".xls"]:
        if pd is None:
            raise ImportError("엑셀 저장에는 pandas/openpyxl이 필요합니다. pip install pandas openpyxl")
        df = pd.DataFrame(rows)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
        df.to_excel(output, index=False)
        return

    with open(output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def generate_keywords(output: str = "keywords.xlsx", append: bool = True, limit: int = 0) -> Path:
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    existing = read_existing(output_path)
    rows = build_rows()

    if limit and limit > 0:
        rows = rows[:limit]

    final = dedupe_rows(existing, rows, append=append)
    save_rows(final, output_path)

    print(f"keywords 저장 완료: {output_path}")
    print(f"총 키워드 수: {len(final)}")
    return output_path


def parse_args():
    parser = argparse.ArgumentParser(description="V5-0 키워드 생성 엔진")
    parser.add_argument("--output", default="keywords.xlsx", help="저장 파일명")
    parser.add_argument("--limit", type=int, default=0, help="생성 개수 제한")
    parser.add_argument("--append", action="store_true", help="기존 keywords에 추가")
    parser.add_argument("--replace", action="store_true", help="기존 파일 대체")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    append = True
    if args.replace:
        append = False
    elif args.append:
        append = True

    generate_keywords(output=args.output, append=append, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
