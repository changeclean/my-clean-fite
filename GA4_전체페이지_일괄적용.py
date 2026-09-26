# -*- coding: utf-8 -*-
"""
체인지클린 기존 HTML 전체에 GA4를 일괄 적용합니다.
사용법:
  1) 이 파일을 사이트 최상위 폴더(예: my-clean-fite)에 넣습니다.
  2) 터미널에서: python GA4_전체페이지_일괄적용.py
  3) 완료 후 git add/commit/push 또는 기존 배포 방식으로 배포합니다.

- 측정 ID: G-LHHLJVRM35
- 이미 같은 GA4가 들어간 HTML은 건너뜁니다.
- <head>가 있는 .html 파일만 수정합니다.
"""

from pathlib import Path

ROOT = Path(".")
GA_ID = "G-LHHLJVRM35"

GA_TAG = f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
"""

def main():
    html_files = list(ROOT.rglob("*.html"))
    changed = 0
    skipped = 0
    no_head = 0
    errors = 0

    print(f"검색된 HTML: {len(html_files)}개")
    print(f"GA4 측정 ID: {GA_ID}")
    print("-" * 50)

    for path in html_files:
        try:
            text = path.read_text(encoding="utf-8")

            if GA_ID in text:
                skipped += 1
                continue

            if "<head>" not in text:
                no_head += 1
                print(f"[HEAD 없음] {path}")
                continue

            new_text = text.replace("<head>", "<head>\n" + GA_TAG, 1)
            path.write_text(new_text, encoding="utf-8", newline="\n")
            changed += 1

            if changed <= 20 or changed % 500 == 0:
                print(f"[적용] {path}")

        except Exception as e:
            errors += 1
            print(f"[오류] {path}: {e}")

    print("\n===== GA4 일괄 적용 완료 =====")
    print("전체 HTML :", len(html_files))
    print("신규 적용 :", changed)
    print("기존 적용 :", skipped)
    print("HEAD 없음 :", no_head)
    print("오류      :", errors)

    if changed:
        print("\n이제 사이트를 배포하면 GA4에서 접속 데이터가 수집됩니다.")
    else:
        print("\n새로 수정된 파일이 없습니다.")

if __name__ == "__main__":
    main()
