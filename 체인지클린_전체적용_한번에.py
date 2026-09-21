# -*- coding: utf-8 -*-
"""
체인지클린 전체 한번에 적용
1) 기존 HTML 전체 최종 보정
2) 앞으로 사용할 하루 50개 생성기 존재 확인
3) Git add / commit / push
"""
from pathlib import Path
import subprocess, sys

BASE = Path(__file__).resolve().parent
PATCH = BASE / "apply_live_estimate_all_FINAL.py"
DAILY = BASE / "daily_50_posts_buyer_longtail_LIVE_SEO_FINAL.py"

def run(cmd):
    print("\n▶", " ".join(cmd))
    r = subprocess.run(cmd, cwd=BASE)
    if r.returncode != 0:
        raise SystemExit("실행 중단: " + " ".join(cmd))

if not PATCH.exists():
    raise SystemExit("파일 없음: " + PATCH.name)
if not DAILY.exists():
    raise SystemExit("파일 없음: " + DAILY.name)

print("=== 체인지클린 전체 한번에 적용 시작 ===")
print("기존 페이지 전체 보정 + 하루 50개 생성기 유지 + Git 배포")

# 기존 페이지 전체 수정
run([sys.executable, PATCH.name, "--root", "."])

# 앞으로 일일 생성기는 FINAL 파일 자체를 Git에 포함.
# 여기서 새 게시글 50개를 즉시 생성하지는 않음.
print("\n✓ 앞으로 하루 50개 생성기:", DAILY.name)

# 배포
run(["git", "add", "."])

# 변경이 있을 때만 commit
check = subprocess.run(["git","diff","--cached","--quiet"], cwd=BASE)
if check.returncode == 0:
    print("\n✓ Git에 새 변경사항이 없어 commit은 생략합니다.")
else:
    run(["git", "commit", "-m", "실시간 견적문의 검색최적화 전체 적용"])

run(["git", "push"])

print("\n=== 완료 ===")
print("✓ 기존 페이지 전체 최종 보정")
print("✓ 하루 50개 FINAL 생성기 포함")
print("✓ GitHub push 완료")
print("✓ Netlify는 연결된 사이트에서 자동 배포")
