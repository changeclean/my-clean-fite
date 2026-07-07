# -*- coding: utf-8 -*-
"""
V5 원클릭 배포 엔진 : deploy.py

이 파일 하나로 전체 실행:
    python deploy.py

실행 흐름
1. keyword_engine_v5.py 실행 → keywords.xlsx 생성/업데이트
2. make_sites_v5.py 실행 → 개별 SEO 페이지 생성
3. main_deploy_v5_pro_plus.py 실행 → 메인/카테고리/sitemap/robots/Git push
4. Netlify 자동 배포

테스트:
    python deploy.py --limit 100 --no-git

키워드 추가 없이 기존 keywords.xlsx만 사용:
    python deploy.py --skip-keywords

전체 재생성:
    python deploy.py --force
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent


def run_cmd(cmd, title: str) -> int:
    print("\n" + "=" * 70)
    print(title)
    print("$ " + " ".join(cmd))
    print("=" * 70)

    result = subprocess.run(cmd, cwd=BASE_DIR, shell=False)

    if result.returncode != 0:
        print(f"\n오류 발생: {title}")
        print(f"종료 코드: {result.returncode}")
        return result.returncode

    print(f"완료: {title}")
    return 0


def file_check() -> bool:
    required = [
        "make_sites_v5.py",
        "main_deploy_v5_pro_plus.py",
        "home_template.html",
        "template.html",
    ]

    missing = []
    for name in required:
        if not (BASE_DIR / name).exists():
            missing.append(name)

    if missing:
        print("필수 파일이 없습니다:")
        for name in missing:
            print("-", name)
        print("\n특히 기존 index.html은 template.html로 이름 변경해야 합니다.")
        return False

    return True


def parse_args():
    parser = argparse.ArgumentParser(description="V5 원클릭 키워드 생성 + 사이트 생성 + 배포")
    parser.add_argument("--skip-keywords", action="store_true", help="키워드 생성 건너뛰기")
    parser.add_argument("--limit", type=int, default=0, help="테스트용 키워드/페이지 개수 제한")
    parser.add_argument("--force", action="store_true", help="페이지 전체 강제 재생성")
    parser.add_argument("--no-git", action="store_true", help="Git push 없이 로컬 생성만")
    parser.add_argument("--dry-run", action="store_true", help="main_deploy Git dry-run")
    parser.add_argument("--message", default="", help="Git commit 메시지")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not file_check():
        return 1

    py = sys.executable

    # 1) 키워드 생성
    if not args.skip_keywords:
        cmd = [py, "keyword_engine_v5.py", "--append"]
        if args.limit:
            cmd += ["--limit", str(args.limit)]

        code = run_cmd(cmd, "1단계: 키워드 생성/중복 제거")
        if code:
            return code
    else:
        print("키워드 생성 건너뜀")

    # 2) SEO 페이지 생성
    cmd = [py, "make_sites_v5.py"]
    if args.limit:
        cmd += ["--limit", str(args.limit)]
    if args.force:
        cmd += ["--force"]

    code = run_cmd(cmd, "2단계: SEO 페이지 생성")
    if code:
        return code

    # 3) 메인/카테고리/사이트맵/Git
    cmd = [py, "main_deploy_v5_pro_plus.py"]
    if args.no_git:
        cmd += ["--no-git"]
    if args.dry_run:
        cmd += ["--dry-run"]

    msg = args.message or f"V5 one-click deploy {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    cmd += ["--message", msg]

    code = run_cmd(cmd, "3단계: 메인/카테고리/사이트맵/Git 배포")
    if code:
        return code

    print("\n전체 완료")
    print("확인 주소:")
    print("https://changeclean1.netlify.app/")
    print("https://changeclean1.netlify.app/sitemap.xml")
    print("https://changeclean1.netlify.app/robots.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
