"""
content_engine_v4.py
중복을 줄이는 청소업체용 본문 생성 엔진
"""

from __future__ import annotations

import random
from datetime import date
from pathlib import Path
from typing import Dict, List


BRAND = "체인지클린"
PHONE = "1688-6751"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


OPENINGS = [
    "{area}에서 {service} 문의를 주신 고객님 댁에 방문해 현장 상태를 꼼꼼히 확인했습니다.",
    "{area} {service}는 구조와 오염도에 따라 작업 순서가 달라지므로 사전 점검이 중요합니다.",
    "이번 현장은 {area}에 위치한 {building} 공간으로, 생활 흔적과 먼지 제거가 핵심이었습니다.",
    "{area} 고객님께서는 보이지 않는 구석까지 깔끔한 {service}를 원하셨습니다.",
    "{area} 지역은 주거 형태가 다양해 현장별 맞춤 작업이 필요합니다.",
    "입주와 이사 일정이 겹치는 현장은 시간 관리와 최종 검수가 특히 중요합니다.",
]

PROCESS = [
    "창틀과 베란다는 미세먼지와 흙먼지가 쌓이기 쉬워 틈새 브러시와 전용 도구로 정리했습니다.",
    "주방은 후드, 싱크대, 배수구, 가스레인지 주변의 기름때를 충분히 불린 뒤 제거했습니다.",
    "욕실은 타일 사이, 수전 주변, 배수구, 환풍기 커버 등 물때가 생기기 쉬운 부분을 중심으로 관리했습니다.",
    "바닥은 소재에 맞춰 물 사용량을 조절하고 손상이 생기지 않도록 단계별로 닦았습니다.",
    "수납장 내부, 문틀, 몰딩, 콘센트 주변처럼 놓치기 쉬운 부분도 함께 점검했습니다.",
    "배수구와 환기구는 가능한 범위 안에서 분리해 세척하고 냄새 원인을 줄이는 방식으로 진행했습니다.",
    "전체 작업 후에는 동선을 따라 재검수하며 먼지 잔여 구역을 다시 확인했습니다.",
]

REVIEWS = [
    "고객님께서는 창틀과 욕실 부분이 특히 깔끔해졌다고 말씀해 주셨습니다.",
    "작업 전과 비교했을 때 공간의 밝기와 쾌적함이 확실히 달라졌습니다.",
    "입주 전 걱정하셨던 먼지와 냄새가 줄어 만족도가 높았습니다.",
    "주방과 욕실처럼 오염도가 높은 구역을 집중적으로 정리해 체감 차이가 컸습니다.",
]

CLOSINGS = [
    "{BRAND}은 빠른 작업보다 꼼꼼한 마감과 최종 검수를 더 중요하게 생각합니다.",
    "{area}에서 {service}를 준비 중이라면 현장 사진과 일정만 알려주셔도 상담 가능합니다.",
    "보이지 않는 곳까지 내 집처럼 확인하는 것이 {BRAND}의 기본 원칙입니다.",
    "상담이 필요하시면 {PHONE}으로 연락 주시면 됩니다.",
]


def ctx(page: Dict[str, str]) -> Dict[str, str]:
    return {
        "keyword": page.get("keyword") or "",
        "area": page.get("area") or "해당 지역",
        "service": page.get("service") or "청소",
        "building": page.get("building") or "주거",
        "intent": page.get("intent") or "전문업체",
        "pyeong": page.get("pyeong") or "",
        "BRAND": BRAND,
        "PHONE": PHONE,
    }


def fmt(sentence: str, c: Dict[str, str]) -> str:
    return sentence.format(**c)


def paragraph(sentences: List[str], c: Dict[str, str], n: int) -> str:
    return " ".join(fmt(s, c) for s in random.sample(sentences, min(n, len(sentences))))


def collect_images() -> List[str]:
    root = Path(__file__).resolve().parent
    images = []
    for d in [root / "images", root / "my_template" / "images"]:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                images.append(p.name)
    return sorted(list(dict.fromkeys(images)))


def image_block(page: Dict[str, str]) -> str:
    images = collect_images()
    if not images:
        return ""

    c = ctx(page)
    picked = random.sample(images, min(3, len(images)))
    alt = f"{c['area']} {c['building']} {c['service']} 현장"

    out = ["<section class='seo-image-block'><h2>현장 이미지</h2><div class='image-grid'>"]
    for img in picked:
        out.append(f'<figure><img src="../images/{img}" alt="{alt}"><figcaption>{alt}</figcaption></figure>')
    out.append("</div></section>")
    return "\n".join(out)


def main_content(page: Dict[str, str]) -> str:
    c = ctx(page)
    keyword = c["keyword"]

    return f"""
<section class="seo-content">
  <h1>{keyword}</h1>
  <p>{paragraph(OPENINGS, c, 2)}</p>

  <h2>{c['area']} {c['service']} 작업 포인트</h2>
  <ul>
    {''.join(f'<li>{fmt(s, c)}</li>' for s in random.sample(PROCESS, min(5, len(PROCESS))))}
  </ul>

  <h2>{c['building']} 청소에서 중요한 부분</h2>
  <p>{paragraph(PROCESS, c, 3)}</p>

  <h2>현장 마무리와 검수</h2>
  <p>{paragraph(REVIEWS, c, 2)} {paragraph(CLOSINGS, c, 2)}</p>
</section>
""".strip()


def feedback(page: Dict[str, str]) -> str:
    c = ctx(page)
    return " ".join([
        paragraph(OPENINGS, c, 1),
        paragraph(PROCESS, c, 2),
        paragraph(REVIEWS, c, 1),
        paragraph(CLOSINGS, c, 1),
    ])


def build_content_pack(page: Dict[str, str], pages: List[Dict[str, str]] | None = None) -> Dict[str, str]:
    return {
        "{{본문}}": main_content(page),
        "{{작업내용}}": main_content(page),
        "{{피드백}}": feedback(page),
        "{{이미지블록}}": image_block(page),
        "{{이미지ALT}}": f"{ctx(page)['area']} {ctx(page)['building']} {ctx(page)['service']} 현장",
        "{{브랜드명}}": BRAND,
        "{{전화번호}}": PHONE,
        "{{작성일}}": date.today().strftime("%Y-%m-%d"),
    }
