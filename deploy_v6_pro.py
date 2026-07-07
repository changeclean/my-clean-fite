# -*- coding: utf-8 -*-
"""
deploy_v6_pro.py

V6 Pro 전용 원클릭 배포 파일
기존 deploy_v6.py가 make_sites_v5.py를 호출해서 템플릿이 다시 덮이는 문제를 해결합니다.

실행:
python deploy_v6_pro.py --skip-keywords --no-git
python deploy_v6_pro.py --skip-keywords
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
SITE_URL = "https://changeclean1.netlify.app"


def run_cmd(cmd, title):
    print("\n" + "=" * 76)
    print(title)
    print("$ " + " ".join(cmd))
    print("=" * 76)
    result = subprocess.run(cmd, cwd=BASE_DIR, shell=False)
    if result.returncode != 0:
        print(f"오류 발생: {title} / code={result.returncode}")
    return result.returncode


def check_files():
    required = [
        "make_sites_v6_pro.py",
        "deploy_v6.py",
        "template.html",
    ]
    missing = []
    for name in required:
        if not (BASE_DIR / name).exists():
            missing.append(name)

    if missing:
        print("필수 파일이 없습니다:")
        for m in missing:
            print("-", m)
        return False
    return True


def parse_args():
    parser = argparse.ArgumentParser(description="V6 Pro 원클릭 배포")
    parser.add_argument("--skip-keywords", action="store_true", help="키워드 생성 건너뛰기")
    parser.add_argument("--limit", type=int, default=0, help="테스트용 페이지 수")
    parser.add_argument("--force", action="store_true", help="전체 강제 재생성")
    parser.add_argument("--no-git", action="store_true", help="Git push 없이 로컬 생성")
    parser.add_argument("--message", default="", help="Git commit 메시지")
    return parser.parse_args()


def main():
    args = parse_args()
    py = sys.executable

    if not check_files():
        return 1

    # 1. 키워드 생성
    if not args.skip_keywords and (BASE_DIR / "keyword_engine_v5.py").exists():
        cmd = [py, "keyword_engine_v5.py", "--append"]
        if args.limit:
            cmd += ["--limit", str(args.limit)]
        code = run_cmd(cmd, "1단계: 키워드 생성")
        if code:
            return code
    else:
        print("키워드 생성 건너뜀")

    # 2. 반드시 make_sites_v6_pro.py 실행
    cmd = [py, "make_sites_v6_pro.py", "--force"]
    if args.limit:
        cmd += ["--limit", str(args.limit)]

    code = run_cmd(cmd, "2단계: V6 Pro 페이지 생성")
    if code:
        return code

    # 3. deploy_v6.py는 페이지 생성 없이 사이트맵/메인용으로만 실행해야 하지만
    # 기존 deploy_v6.py가 make_sites_v5.py를 호출할 수 있으므로 직접 호출하지 않습니다.
    # 대신 Git 배포만 여기서 처리합니다.
    print("\n페이지 생성 완료.")
    print("이제 sitemap/rss는 기존 deploy_v6.py가 아닌, 현재 생성된 deploys 기준으로 유지됩니다.")
    print("사이트맵을 새로 만들려면 deploy_v6.py 내부 make_sites_v5.py 호출을 make_sites_v6_pro.py로 바꿔야 합니다.")

    if args.no_git:
        print("Git 배포는 건너뛰었습니다.")
        print("확인: deploys 폴더의 페이지를 직접 열어 {{지역명}}이 사라졌는지 확인하세요.")
        return 0

    msg = args.message or f"V6 Pro deploy {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    for cmd in [
        ["git", "add", "."],
        ["git", "commit", "-m", msg],
        ["git", "push"],
    ]:
        code = run_cmd(cmd, "Git 배포: " + " ".join(cmd))
        if code:
            return code

    print("\n전체 완료")
    print(SITE_URL)
    print(SITE_URL + "/sitemap.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
