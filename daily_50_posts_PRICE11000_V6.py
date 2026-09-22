#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
체인지클린 청소업체찾기 - 하루 50개 게시글 생성기

안전 원칙
- 기존 루트 SEO index.html은 수정하지 않음
- 기존 게시글은 덮어쓰지 않음
- 실행당 기본 50개
- 날짜를 게시글 화면에 표시하지 않음
- cleaning-company/index.html을 게시글 목록으로 관리
- 상태파일로 다음 대상 페이지를 이어서 순환
- --no-git 지원
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
COUNT_DEFAULT = 50
SITE_URL = "https://clever-griffin-93819d.netlify.app"
PHONE_MAIN = "1688-6751"
PHONE_DIRECT = "010-6811-3176"
FORMSPREE = "https://formspree.io/f/mvzlylrr"

STATE_FILE = BASE_DIR / "daily_50_state.json"
LOG_FILE = BASE_DIR / "daily_50_log.jsonl"
ASSET_DIR = BASE_DIR / "assets" / "cleaning-ai"

ARTICLE_TOPICS = [
    ("입주청소 잘하는곳", "movein-cleaning-best"),
    ("입주청소 업체 추천", "movein-cleaning-company"),
    ("입주청소 가격", "movein-cleaning-price"),
    ("입주청소 비용", "movein-cleaning-cost"),
    ("입주청소 견적", "movein-cleaning-estimate"),
    ("입주청소 업체", "movein-cleaning-service"),
    ("이사청소 잘하는곳", "moving-cleaning-best"),
    ("이사청소 업체 추천", "moving-cleaning-company"),
    ("이사청소 가격", "moving-cleaning-price"),
    ("이사청소 비용", "moving-cleaning-cost"),
    ("이사청소 견적", "moving-cleaning-estimate"),
    ("이사청소 업체", "moving-cleaning-service"),
    ("원룸 입주청소 업체", "oneroom-movein-company"),
    ("원룸 이사청소 업체", "oneroom-moving-company"),
    ("원룸 청소 비용", "oneroom-cleaning-cost"),
    ("오피스텔 입주청소 업체", "officetel-movein-company"),
    ("오피스텔 이사청소 업체", "officetel-moving-company"),
    ("오피스텔 청소 비용", "officetel-cleaning-cost"),
    ("아파트 입주청소 업체", "apartment-movein-company"),
    ("아파트 입주청소 가격", "apartment-movein-price"),
    ("아파트 입주청소 견적", "apartment-movein-estimate"),
    ("아파트 이사청소 업체", "apartment-moving-company"),
    ("아파트 이사청소 비용", "apartment-moving-cost"),
    ("빌라 입주청소 업체", "villa-movein-company"),
    ("빌라 이사청소 업체", "villa-moving-company"),
    ("투룸 입주청소 업체", "tworoom-movein-company"),
    ("쓰리룸 입주청소 업체", "threeroom-movein-company"),
    ("거주청소 업체", "residential-cleaning-company"),
    ("거주청소 비용", "residential-cleaning-cost"),
    ("사무실 청소업체", "office-cleaning-company"),
    ("상가 청소업체", "store-cleaning-company"),
    ("청소업체 견적 비교", "cleaning-company-compare"),
    ("청소업체 추천", "cleaning-company-recommend"),
    ("청소업체 잘하는곳", "cleaning-company-best"),
    ("청소업체 전화번호", "cleaning-company-phone"),
    ("청소업체 상담", "cleaning-company-contact"),
    ("당일 입주청소 업체", "same-day-movein-cleaning"),
    ("급한 입주청소 업체", "urgent-movein-cleaning"),
    ("주말 입주청소 업체", "weekend-movein-cleaning"),
    ("주말 이사청소 업체", "weekend-moving-cleaning"),
    ("신축아파트 입주청소 업체", "new-apartment-movein"),
    ("구축아파트 이사청소 업체", "old-apartment-moving"),
    ("입주청소 후기 좋은곳", "movein-cleaning-review"),
    ("이사청소 후기 좋은곳", "moving-cleaning-review"),
    ("입주청소 저렴한곳", "movein-cleaning-affordable"),
    ("이사청소 저렴한곳", "moving-cleaning-affordable"),
    ("입주청소 예약", "movein-cleaning-booking"),
    ("이사청소 예약", "moving-cleaning-booking"),
    ("입주청소 문의", "movein-cleaning-contact"),
    ("이사청소 문의", "moving-cleaning-contact"),
]
def esc(v): return html.escape(str(v), quote=True)

def read_text(p):
    return p.read_text(encoding="utf-8", errors="replace")

def write_text(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def detect_keyword(content: str, folder: str) -> str:
    # 두 기존 템플릿 모두 h1을 우선 사용
    m = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.I | re.S)
    if m:
        txt = re.sub(r"<[^>]+>", " ", m.group(1))
        txt = html.unescape(re.sub(r"\s+", " ", txt)).strip()
        txt = re.sub(r"깨끗함이 바뀌는 체인지클린", "", txt).strip()
        if txt:
            return txt
    m = re.search(r"<title[^>]*>(.*?)</title>", content, re.I | re.S)
    if m:
        txt = html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))
        txt = re.sub(r"\s+", " ", txt).strip()
        txt = re.sub(r"\s*[|｜].*$", "", txt).strip()
        if txt:
            return txt
    return folder.replace("-", " ")

def find_targets():
    ignored = {".git", ".github", "assets", "images", "__pycache__", "node_modules"}
    targets = []
    for d in BASE_DIR.iterdir():
        if not d.is_dir() or d.name in ignored or d.name.startswith("."):
            continue
        root = d / "index.html"
        board = d / "cleaning-company"
        if root.exists() and board.exists():
            c = read_text(root)
            # 두 템플릿을 모두 허용. 띠 링크가 있는 현재 운영 페이지 우선.
            if "cleaning-company/" in c or 'id="services"' in c or "content-images" in c:
                targets.append((d.name, detect_keyword(c, d.name)))
    return sorted(targets)

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(read_text(STATE_FILE))
        except Exception:
            pass
    return {"cursor": 0, "round": 1}

def save_state(cursor, round_no):
    write_text(STATE_FILE, json.dumps({
        "cursor": cursor, "round": round_no,
        "updated_at": datetime.now().isoformat(timespec="seconds")
    }, ensure_ascii=False, indent=2))

def image_files():
    if not ASSET_DIR.exists():
        return []
    return sorted([p for p in ASSET_DIR.iterdir()
                   if p.is_file() and p.suffix.lower() in {".webp",".jpg",".jpeg",".png"}])

def image_rel(article_dir: Path, image: Path):
    return Path("../../../assets/cleaning-ai") / image.name


def clean_location_keyword(keyword: str) -> str:
    """
    기존 SEO H1에서 지역 부분만 최대한 자연스럽게 추출합니다.
    예:
    경기 안산시 상록구 팔곡일동 원룸청소 오피스텔 체인지클린 청소업체찾기
    -> 경기 안산시 상록구 팔곡일동
    """
    s = html.unescape(re.sub(r"<[^>]+>", " ", keyword))
    s = re.sub(r"\s+", " ", s).strip()

    # 브랜드/목록성 표현 제거
    s = re.sub(r"체인지클린|내집클린|1등청소|청소업체찾기|청소업체|청소전문", " ", s)

    # 서비스 키워드가 시작되는 지점부터 잘라 지역명만 남김
    service_markers = [
        "입주청소", "이사청소", "거주청소", "원룸청소", "오피스텔",
        "아파트청소", "아파트", "빌라청소", "빌라", "투룸", "쓰리룸",
        "상가청소", "사무실청소", "특수청소", "청소"
    ]
    cut = len(s)
    for marker in service_markers:
        pos = s.find(marker)
        if pos != -1:
            cut = min(cut, pos)
    s = s[:cut]
    s = re.sub(r"\s+", " ", s).strip(" -|")

    return s or keyword.strip()


def make_longtail_title(keyword: str, topic: str) -> str:
    location = clean_location_keyword(keyword)
    return f"{location} {topic}".strip()

def article_body(keyword, topic, seed):
    rng = random.Random(seed)
    intros = [
        f"{keyword}를 알아볼 때는 단순히 가격만 비교하기보다 공간 구조와 실제 청소범위를 함께 확인하는 것이 좋습니다.",
        f"{keyword} 관련 상담에서는 평수뿐 아니라 방·화장실 수, 짐 유무, 오염 상태와 원하는 작업 범위를 같이 확인해야 견적 차이를 줄일 수 있습니다.",
        f"{keyword} 업체를 찾는 분들이 자주 궁금해하는 부분은 비용, 작업시간, 기본 청소범위와 추가 작업 여부입니다.",
    ]
    sections = [
        ("견적 전에 확인할 내용",
         "같은 평수라도 공간 구조와 오염 상태에 따라 작업량이 달라질 수 있습니다. 상담할 때 주소와 공간 종류, 평수 또는 면적, 방과 화장실 개수, 베란다 유무, 짐과 폐기물 유무를 알려주면 보다 정확하게 범위를 확인할 수 있습니다. 신축 분진이 많은 입주 현장과 기존 생활오염이 남아 있는 이사 현장은 중점 작업 구역도 달라질 수 있습니다."),
        ("기본적으로 살펴볼 청소범위",
         "현관과 신발장, 방과 거실, 몰딩과 문틀, 주방 수납장과 후드 외부, 욕실과 배수구 주변, 베란다와 창틀, 바닥과 모서리 등을 순서대로 확인합니다. 수납공간은 내부까지 작업하는지, 창문은 내창과 창틀 중 어디까지 포함되는지처럼 업체마다 기준이 달라질 수 있는 항목은 예약 전에 확인하는 편이 좋습니다."),
        ("주방과 욕실",
         "주방은 기름때와 수납장 안쪽 먼지, 싱크대 주변 오염을 확인하고 욕실은 물때와 배수구, 수전, 타일 표면 등을 살펴봅니다. 오래된 고착 오염이나 변색, 손상된 실리콘처럼 일반 세척만으로 원상복구가 어려운 부분은 청소 결과와 별개로 구분해서 보는 것이 좋습니다."),
        ("창틀·베란다와 바닥",
         "창틀에는 외부 먼지와 분진이 쌓이기 쉽고 베란다는 배수구 주변이나 모서리에 오염이 남기 쉽습니다. 바닥은 위쪽 먼지 제거와 다른 구역 세척이 끝난 뒤 마무리하는 방식이 효율적입니다. 외창처럼 안전장비가 필요한 구역은 기본 범위에서 제외될 수 있으므로 사전에 포함 여부를 확인해야 합니다."),
        ("예약할 때 체크할 부분",
         "희망 날짜와 입실 또는 이사 시간을 미리 알려주고 주차 가능 여부와 엘리베이터 사용 조건도 함께 확인하면 작업 당일 진행이 수월합니다. 현장 사진이 있다면 오염이 심한 구역이나 특이사항을 상담할 때 함께 전달하는 것도 도움이 됩니다."),
        ("체인지클린 상담 안내",
         f"체인지클린은 입주청소, 이사청소, 거주청소, 원룸·오피스텔·빌라·아파트 청소와 상가·사무실 청소를 상담하고 있습니다. {keyword} 관련해서도 현장 정보를 확인한 뒤 필요한 작업 범위와 일정을 안내해드립니다. 정확한 견적은 공간 상태와 요청 범위를 확인한 후 상담하는 방식이 가장 좋습니다."),
    ]
    rng.shuffle(sections)
    sections.append((
        topic,
        f"{keyword} 검색 시에는 광고 문구보다 실제로 어디까지 청소하는지, 추가 비용이 생기는 조건은 무엇인지, 작업 후 검수는 어떻게 진행하는지를 비교해보는 것이 좋습니다. 특히 평수만으로 모든 현장의 작업량을 판단하기 어려우므로 구조와 오염 상태를 함께 전달해 상담받는 것이 좋습니다."
    ))
    return rng.choice(intros), sections


def price11000_card(topic):
    if "입주청소" not in topic and "이사청소" not in topic:
        return ""
    service = "입주청소" if "입주청소" in topic else "이사청소"
    return f"""<section style="background:#f3f8ff;border:1px solid #d9e9fb;border-radius:18px;padding:24px 20px;margin:28px 0;text-align:center"><div style="font-weight:800;color:#1769c2">체인지클린 {esc(service)} 예상비용</div><h2 style="color:#111827">{esc(service)} 평당 11,000원</h2><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px"><div style="background:#fff;border-radius:12px;padding:15px"><b>25평</b><br><strong>275,000원</strong></div><div style="background:#fff;border-radius:12px;padding:15px"><b>34평</b><br><strong>374,000원</strong></div><div style="background:#fff;border-radius:12px;padding:15px"><b>40평</b><br><strong>440,000원</strong></div></div><p style="font-size:13px;color:#64748b">※ 현장 상태·구조·오염도·추가 작업에 따라 최종 견적은 달라질 수 있습니다.</p></section>"""

def make_article(parent_slug, keyword, topic, post_slug, seq, imgs):
    canonical = f"{SITE_URL}/{parent_slug}/cleaning-company/{post_slug}/"
    chosen = []
    if imgs:
        start = int(hashlib.sha256((parent_slug+post_slug).encode()).hexdigest()[:8], 16) % len(imgs)
        n = min(4, len(imgs))
        chosen = [imgs[(start+i*17) % len(imgs)] for i in range(n)]

    article_keyword = f"{clean_location_keyword(keyword)} {topic}".strip()
    intro, sections = article_body(article_keyword, topic, parent_slug + post_slug)

    # 본문 사이에 사진을 분산 배치: 글 → 사진 → 글 → 사진 ...
    content_parts = [f'<div class="intro-card"><p>{esc(intro)}</p></div>']
    image_index = 0
    for sec_index, (heading, paragraph) in enumerate(sections):
        content_parts.append(
            f'<section class="article-card"><h2>{esc(heading)}</h2><p>{esc(paragraph)}</p></section>'
        )
        # 첫 4개 주요 섹션 뒤에 이미지 1장씩 배치
        if image_index < len(chosen) and sec_index in (0, 1, 2, 3):
            img = chosen[image_index]
            image_index += 1
            content_parts.append(f"""
            <figure class="ba-figure">
              <img src="../../../assets/cleaning-ai/{esc(img.name)}" loading="lazy"
                   alt="{esc(keyword)} {esc(topic)} 청소 전후 예시 이미지 {image_index}">
              <figcaption>※ 청소 전후 예시 이미지(AI 생성)이며 실제 고객 현장 사진이 아닙니다.</figcaption>
            </figure>""")
    body = "\n".join(content_parts)
    price_card = price11000_card(topic)
    if price_card:
        body += "\n" + price_card

    location = clean_location_keyword(keyword)
    is_price_service = ("입주청소" in topic or "이사청소" in topic)
    if is_price_service:
        service = "입주청소" if "입주청소" in topic else "이사청소"
        title = f"{location} {service} 가격 | 평당 11,000원 체인지클린".strip()
        desc = f"{location} {service} 평당 11,000원 기준. 평수별 예상비용과 청소범위를 확인하고 간편하게 견적을 신청하세요."
    else:
        title = make_longtail_title(keyword, topic)
        desc = f"{title} 비용과 청소범위, 예약 전 확인사항을 확인하고 체인지클린에 빠르게 견적을 신청하세요."

    og_image = f"{SITE_URL}/assets/cleaning-ai/{chosen[0].name}" if chosen else f"{SITE_URL}/assets/og-cleaning.jpg"
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc[:160])}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="article">
<meta property="og:site_name" content="체인지클린">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc[:160])}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{esc(og_image)}">
<link rel="canonical" href="{esc(canonical)}">
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,"Noto Sans KR","Malgun Gothic",sans-serif;color:#1f2937;line-height:1.8;background:#fff}}
a{{color:inherit}}.wrap{{max-width:860px;margin:auto;padding:24px 20px}}header{{background:#075fce;color:#fff;padding:34px 20px}}header .in{{max-width:860px;margin:auto}}
h1{{font-size:32px;line-height:1.35;margin:8px 0}}h2{{font-size:23px;color:#075fce;margin:0 0 10px}}p{{font-size:17px;margin:0}}
.intro-card{{background:#eef6ff;border-left:5px solid #075fce;border-radius:14px;padding:20px;margin:18px 0 26px}}
.article-card{{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:22px;margin:24px 0;box-shadow:0 6px 20px rgba(15,23,42,.05)}}
.ba-figure{{margin:24px 0 34px}}.ba-figure img{{width:100%;display:block;border-radius:16px;box-shadow:0 8px 24px rgba(15,23,42,.08)}}.ba-figure figcaption{{font-size:13px;color:#6b7280;margin-top:8px}}
.top-actions{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:14px}}.direct{{display:inline-block;background:#fff;color:#075fce;padding:10px 15px;border-radius:10px;font-weight:900;text-decoration:none}}.fast-estimate{{display:inline-block;background:#ffcc00;color:#111;padding:10px 15px;border-radius:10px;font-weight:900;text-decoration:none}}
figure{{margin:30px 0}}figure img{{width:100%;display:block;border-radius:15px}}figcaption{{font-size:13px;color:#6b7280;margin-top:7px}}
.cta{{background:#eef6ff;border:1px solid #bfdbfe;padding:22px;border-radius:16px;margin:35px 0;text-align:center}}.cta a{{font-weight:900;color:#075fce}}
.form{{background:#f8fafc;padding:22px;border-radius:16px}}label{{display:block;font-weight:800;margin:12px 0 5px}}
input,select,textarea{{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:8px;font:inherit}}button{{width:100%;margin-top:15px;padding:14px;border:0;border-radius:9px;background:#075fce;color:#fff;font-size:17px;font-weight:900}}
.links{{margin:32px 0;padding:0;list-style:none}}.links li{{margin:8px 0}}.links a{{color:#075fce}}
.back{{display:inline-block;margin-bottom:20px;color:#075fce;font-weight:800}}footer{{text-align:center;background:#075fce;color:#fff;padding:25px}}
.live-box{{margin:22px 0 30px;border:1px solid #dbeafe;border-radius:18px;overflow:hidden;box-shadow:0 10px 28px rgba(15,23,42,.08);background:#fff}}
.live-head{{background:#075fce;color:#fff;padding:14px 18px;font-size:19px;font-weight:900}}
.live-window{{height:260px;overflow:hidden;cursor:pointer;position:relative}}
.live-track{{animation:liveScroll 32s linear infinite;will-change:transform}}
.live-row{{height:65px;display:grid;grid-template-columns:70px 1fr 1fr 90px 70px;gap:8px;align-items:center;padding:0 16px;border-bottom:1px solid #edf2f7;font-size:14px}}
.live-name{{font-weight:900}}.live-time{{color:#64748b;text-align:right;white-space:nowrap}}.live-date{{font-weight:800;color:#075fce;white-space:nowrap}}
@keyframes liveScroll{{from{{transform:translateY(0)}}to{{transform:translateY(-520px)}}}}
@media(max-width:600px){{h1{{font-size:27px}}.wrap{{padding:20px 16px}}.live-window{{height:210px}}.live-row{{height:70px;grid-template-columns:58px 1fr 70px 58px;padding:0 10px;font-size:12px}}.live-service{{display:none}}@keyframes liveScroll{{from{{transform:translateY(0)}}to{{transform:translateY(-560px)}}}}}}
</style>
<style id="cc-live-estimate-v3-fix">
/* V3: only live-estimate area; do not alter article/image overflow globally */
.cc-live-estimate-final,
#cc-live-estimate-final {{
  height:auto !important;
  max-height:none !important;
}}
.cc-live-estimate-final table,
#cc-live-estimate-final table {{
  position:relative !important;
  z-index:1 !important;
  margin-top:18px !important;
}}
</style>

</head><body>
<header><div class="in">
<div>체인지클린 청소업체찾기</div>
<h1>{esc(title)}</h1>
<p>안녕하세요. 꼼꼼한 청소전문 체인지클린입니다~^^<br>깨끗한 변화로 뿌듯함을 안겨드리겠습니다!</p>
<div class="top-actions"><a class="direct" href="tel:01068113176">상담직통 010-6811-3176</a><a class="fast-estimate" href="#estimate-form">⚡ 빠른 견적문의</a></div>
</div></header>
<main class="wrap">
<section class="live-box" onclick="document.getElementById('estimate-form').scrollIntoView({{behavior:'smooth'}})">
  <div class="live-head">● 실시간 견적문의</div>
  <div class="live-window"><div class="live-track" id="liveTrack"></div></div>
</section>
<a class="back" href="../">← 청소업체찾기 글목록</a>
{body}
<div class="cta"><strong>청소 일정과 공간 정보를 알려주세요.</strong><br>
<a href="tel:16886751">대표번호 {PHONE_MAIN}</a> · <a href="tel:01068113176">{PHONE_DIRECT}</a></div>

<section class="form" id="estimate-form"><h2>간편 견적 문의</h2>
<form action="{FORMSPREE}" method="POST">
<input type="hidden" name="유입페이지" value="{esc(title)}">
<input type="hidden" name="_subject" value="체인지클린 청소업체찾기 견적문의">
<label>이름</label><input name="이름" required>
<label>연락처</label><input name="연락처" required placeholder="010-0000-0000">
<label>청소종류</label><select name="청소종류"><option>입주청소</option><option>이사청소</option><option>거주청소</option><option>원룸청소</option><option>상가·사무실청소</option><option>기타</option></select>
<label>평수</label><input name="평수" placeholder="예: 25평">
<label>지역·주소</label><input name="지역·주소">
<label>희망일</label><input type="date" name="희망일">
<label>연락가능시간</label><input name="연락가능시간">
<label>문의내용</label><textarea name="문의내용" rows="4"></textarea>
<button type="submit">무료 견적 신청하기</button>
</form></section>

<ul class="links">
<li><a href="https://litt.ly/changeclean" target="_blank" rel="noopener">체인지클린 살펴보기</a></li>
<li><a href="https://naver.me/G8t13Dk" target="_blank" rel="noopener">체인지클린 확인-주소: 인천 미추홀구 주안로180번길 27-1 (주안동)</a></li>
<li><a href="https://blog.naver.com/changeclean1" target="_blank" rel="noopener">체인지클린 네이버</a></li>
<li><a href="https://changeclean.co.kr" target="_blank" rel="noopener">체인지클린 워드프레스</a></li>
<li><a href="https://changeclean.tistory.com/" target="_blank" rel="noopener">체인지클린 티스토리</a></li>
<li><a href="https://naver.me/5imyvric" target="_blank" rel="noopener">체인지클린 예약</a></li>
<li><a href="https://kko.to/nW6Je-YgpO" target="_blank" rel="noopener">체인지클린 카카오맵</a></li>
</ul>
</main><footer>체인지클린 · 대표번호 {PHONE_MAIN}</footer>
<script>
(function(){{
 const data=[
  ["최*석","인천 송도동","입주청소 · 34평",3,3],
  ["김*영","김포 장기동","이사청소 · 25평",6,8],
  ["박*민","부천 중동","입주청소 · 32평",9,14],
  ["이*희","고양 일산동구","거주청소 · 41평",13,21],
  ["정*호","인천 부평구","이사청소 · 28평",17,37],
  ["한*진","서울 강서구","입주청소 · 34평",21,48],
  ["오*현","인천 계양구","사무실청소",25,62],
  ["강*은","김포 구래동","입주청소 · 30평",29,78]
 ];
 const fmt=d=>`${{d.getMonth()+1}}/${{d.getDate()}}`;
 const today=new Date(); today.setHours(0,0,0,0);
 const rows=data.map(x=>{{
   const d=new Date(today); d.setDate(d.getDate()+x[3]);
   const ago=x[4]<60?`${{x[4]}}분 전`:`${{Math.floor(x[4]/60)}}시간 전`;
   return `<div class="live-row"><span class="live-name">${{x[0]}}</span><span>${{x[1]}}</span><span class="live-service">${{x[2]}}</span><span class="live-date">예약 ${{fmt(d)}}</span><span class="live-time">${{ago}}</span></div>`;
 }}).join("");
 const t=document.getElementById("liveTrack"); if(t) t.innerHTML=rows+rows;
}})();
</script>
</body></html>"""

def existing_posts(board: Path):
    posts = []
    for d in board.iterdir():
        if d.is_dir() and (d/"index.html").exists():
            c = read_text(d/"index.html")
            m = re.search(r"<h1[^>]*>(.*?)</h1>", c, re.I|re.S)
            title = re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else d.name
            posts.append((d.name, html.unescape(title)))
    return sorted(posts, reverse=True)

def make_board(parent_slug, keyword, posts):
    items = "\n".join(
        f'<a class="item" href="./{esc(slug)}/"><strong>{esc(title)}</strong><span>청소범위 · 비용 · 견적 정보 보기 →</span></a>'
        for slug, title in posts
    )
    canonical = f"{SITE_URL}/{parent_slug}/cleaning-company/"
    location = clean_location_keyword(keyword)
    return f"""<!doctype html><html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(location)} 청소정보 | 체인지클린</title>
<meta name="description" content="{esc(location)} 입주청소, 이사청소, 거주청소 비용과 범위, 업체 선택 정보를 확인하세요.">
<link rel="canonical" href="{esc(canonical)}">
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,"Noto Sans KR","Malgun Gothic",sans-serif;background:#f8fafc;color:#1f2937}}
.wrap{{max-width:900px;margin:auto;padding:30px 18px}}h1{{font-size:32px}}.top{{background:#075fce;color:#fff;padding:35px 0}}
.item{{display:block;background:#fff;border:1px solid #dbeafe;border-radius:14px;padding:18px;margin:12px 0;text-decoration:none;color:#111827;box-shadow:0 5px 18px #0f172a0b}}
.item strong{{display:block;font-size:19px}}.item span{{display:block;color:#64748b;margin-top:5px}}.call{{display:block;text-align:center;background:#075fce;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;margin-top:25px}}
</style></head><body>
<div class="top"><div class="wrap"><div>체인지클린</div><h1>{esc(location)} 청소정보</h1><p>지역별 청소범위 · 비용 · 견적 · 예약 전 확인사항</p></div></div>
<main class="wrap">{items}
<a class="call" href="tel:16886751">견적문의 {PHONE_MAIN}</a></main>
</body></html>"""

def git_deploy(n):
    cmds = [
        ["git","add","."],
        ["git","commit","-m",f"청소업체찾기 게시글 {n}개 추가"],
        ["git","push"]
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=BASE_DIR)
        if r.returncode != 0:
            raise RuntimeError("Git 명령 실패: " + " ".join(cmd))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=COUNT_DEFAULT)
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--reset-test", action="store_true",
                    help="테스트 상태를 처음부터 시작합니다. 기존 생성 글은 덮어쓰지 않습니다.")
    args = ap.parse_args()
    count = max(1, args.count)

    targets = find_targets()
    if not targets:
        raise SystemExit("대상 SEO 페이지를 찾지 못했습니다.")
    imgs = image_files()
    state = {"cursor": 0, "round": 1} if args.reset_test else load_state()
    cursor = int(state.get("cursor",0)) % len(targets)
    round_no = max(1, int(state.get("round",1)))

    selected = []
    for i in range(min(count, len(targets))):
        idx = (cursor+i) % len(targets)
        selected.append(targets[idx])

    created = []
    for offset, (parent_slug, keyword) in enumerate(selected):
        board = BASE_DIR / parent_slug / "cleaning-company"
        topic, topic_slug = ARTICLE_TOPICS[(round_no + cursor + offset) % len(ARTICLE_TOPICS)]
        # URL에 날짜를 쓰지 않음. 같은 주제 재순환 시 번호만 추가.
        base_slug = topic_slug
        post_slug = base_slug
        k = 2
        while (board/post_slug).exists():
            post_slug = f"{base_slug}-{k}"
            k += 1
        article = make_article(parent_slug, keyword, topic, post_slug, round_no, imgs)
        write_text(board/post_slug/"index.html", article)
        posts = existing_posts(board)
        write_text(board/"index.html", make_board(parent_slug, keyword, posts))
        created.append(f"{parent_slug}/cleaning-company/{post_slug}/")
        print(f"[{len(created):02d}/{len(selected):02d}] {created[-1]}")

    new_cursor = cursor + len(selected)
    new_round = round_no
    if new_cursor >= len(targets):
        new_cursor %= len(targets)
        new_round += 1
    save_state(new_cursor, new_round)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(created), "round": round_no, "created": created
        }, ensure_ascii=False) + "\n")

    print(f"\n완료: {len(created)}개")
    print(f"다음 시작 위치: {new_cursor+1}/{len(targets)}")
    print("※ 게시글 화면에는 날짜를 표시하지 않습니다.")

    if not args.no_git:
        git_deploy(len(created))
        print("Git push 완료 → Netlify 자동 배포")
    else:
        print("--no-git: Git 배포 생략")

if __name__ == "__main__":
    main()
