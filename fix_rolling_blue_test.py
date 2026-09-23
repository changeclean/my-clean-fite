# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(".")

# 방금 실제 배포 화면에서 확인한 파란 템플릿 중 하나
TARGET = ROOT / "seo-gwang-jayang-dong-cleaning" / "index.html"

if not TARGET.exists():
    # seo- 없는 동일 계열 폴더도 검색
    matches = list(ROOT.glob("*gwang*jayang*cleaning/index.html"))
    if not matches:
        raise SystemExit("테스트 파일을 찾지 못했습니다.")
    TARGET = matches[0]

s = TARGET.read_text(encoding="utf-8", errors="replace")

if "<!-- MAIN_LIVE_ROLLING_V1 -->" not in s:
    raise SystemExit(f"롤링 코드가 없는 파일입니다: {TARGET}")

MARKER = "<!-- BLUE_ROLLING_MOBILE_FIX_V1 -->"

if MARKER in s:
    print("이미 테스트 수정되어 있습니다.")
    print(TARGET)
    raise SystemExit()

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

    /* 롤링을 감싸고 있는 상위 영역이 잘라내지 않도록 보정 */
    body,
    main {
        height:auto !important;
        max-height:none !important;
    }
}
</style>
'''

# </head> 바로 전에 넣어서 기존 CSS보다 뒤에서 우선 적용
if "</head>" not in s.lower():
    raise SystemExit("head 종료 태그를 찾지 못했습니다.")

s = re.sub(
    r"</head>",
    fix + "\n</head>",
    s,
    count=1,
    flags=re.I
)

TARGET.write_text(s, encoding="utf-8")

print()
print("===== 테스트 수정 완료 =====")
print(TARGET)
print("11,000원 박스: 유지")
print("업체찾기 버튼: 유지")
print("기존 롤링 데이터: 유지")
print("모바일 롤링 표시 CSS만 보정")