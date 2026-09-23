# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(".")

PRICE_MARKER = "<!-- MAIN_PRICE_11000_V1 -->"
ROLL_MARKER = "<!-- MAIN_LIVE_ROLLING_V1 -->"
FIX_MARKER = "<!-- BLUE_ROLLING_MOBILE_FIX_V1 -->"

fix = r'''
<!-- BLUE_ROLLING_MOBILE_FIX_V1 -->
<style>
/* 파란 메인 템플릿 - 모바일 롤링 표시 보정 */
@media (max-width: 700px) {

    .cc-main-live {
        display:block !important;
        visibility:visible !important;
        opacity:1 !important;
        position:relative !important;
        z-index:20 !important;

        width:calc(100% - 24px) !important;
        max-width:760px !important;

        height:auto !important;
        min-height:0 !important;
        max-height:none !important;

        margin:16px auto 22px !important;
        overflow:hidden !important;
    }

    .cc-main-live-head {
        display:block !important;
        visibility:visible !important;
        height:auto !important;
        min-height:48px !important;
        padding:13px 14px !important;
    }

    .cc-main-live-window {
        display:block !important;
        visibility:visible !important;
        position:relative !important;

        height:244px !important;
        min-height:244px !important;
        max-height:244px !important;

        overflow:hidden !important;
    }

    .cc-main-live-track {
        display:block !important;
        visibility:visible !important;
        opacity:1 !important;
    }

    .cc-main-live-row {
        display:grid !important;
        visibility:visible !important;
    }

    body,
    main {
        height:auto !important;
        max-height:none !important;
    }
}
</style>
'''

# ------------------------------------------------
# 지역 메인 index.html(depth 2) 중
# 파란 템플릿만 정확히 선택
# ------------------------------------------------

targets = []

for p in ROOT.glob("*/index.html"):

    try:
        s = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue

    # 11,000원 + 롤링 + 업체찾기 버튼이 있는 메인만
    if PRICE_MARKER not in s:
        continue

    if ROLL_MARKER not in s:
        continue

    if "우리 지역 청소업체찾기" not in s:
        continue

    # 신형 3,010개 제외
    if "깨끗함이 바뀌는 체인지클린" in s:
        continue

    targets.append(p)


print("파란 템플릿 대상:", len(targets), "개")

# 안전장치
if len(targets) != 6009:
    raise SystemExit(
        f"중단: 예상 대상 6009개 / 실제 대상 {len(targets)}개"
    )


changed = 0
already = 0
errors = 0

for i, p in enumerate(targets, 1):

    try:
        s = p.read_text(encoding="utf-8", errors="replace")

        # 테스트했던 1개 등 이미 적용된 페이지
        if FIX_MARKER in s:
            already += 1
            continue

        # head 마지막에 넣어 기존 CSS보다 우선 적용
        lower = s.lower()
        pos = lower.find("</head>")

        if pos == -1:
            errors += 1
            print("HEAD 없음:", p)
            continue

        s = s[:pos] + fix + "\n" + s[pos:]

        p.write_text(s, encoding="utf-8")
        changed += 1

    except Exception as e:
        errors += 1
        print("오류:", p, e)

    if i % 500 == 0:
        print(
            f"[{i}/6009] "
            f"수정 {changed} / "
            f"이미정상 {already} / "
            f"오류 {errors}",
            flush=True
        )


print()
print("===== 완료 =====")
print("대상:", len(targets))
print("수정:", changed)
print("이미정상:", already)
print("오류:", errors)

if changed + already == 6009 and errors == 0:
    print("정상: 파란 템플릿 6009개 처리 완료")
else:
    print("확인 필요")
