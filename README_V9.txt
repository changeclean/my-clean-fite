V9 SEO Incremental Engine
=========================

설치 위치
---------
C:\Users\USER\Documents\GitHub\my-clean-fite\V9.py
C:\Users\USER\Documents\GitHub\my-clean-fite\v9_page_template.html

10개 테스트
-----------
cd "C:\Users\USER\Documents\GitHub\my-clean-fite"
python -u .\V9.py --count 10 --no-git

V8에서 이미 만든 10개를 유지하고, 나머지 2,990개 생성
---------------------------------------------------------
python -u .\V9.py --count 2990

기능
----
- 키워드 자동 생성
- 기존 slug 중복 제거
- 루트 index.html 보존
- 기존 페이지 폴더 보존
- 기존 디자인과 이미지 순서 유지
- 본문/후기/FAQ 다양화
- 같은 지역/서비스/공간 유형 중심 내부링크
- 키워드 품질 등급 출력
- sitemap/RSS 갱신
- 현재 Git 브랜치 자동 push
