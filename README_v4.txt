청소업체 SEO CMS v4 사용법

1. 아래 파일들을 프로젝트 폴더에 넣으세요.
- make_sites_v4.py
- keyword_parser_v4.py
- seo_engine_v4.py
- content_engine_v4.py
- link_engine_v4.py
- sitemap_engine_v4.py
- quality_engine_v4.py

2. 같은 폴더에 아래도 있어야 합니다.
- keywords.xlsx
- my_template/index.html
- images 폴더(있으면 자동 복사)

3. 설치
pip install openpyxl

4. 실행
python make_sites_v4.py

5. 변경된 페이지만 생성
python make_sites_v4.py --incremental

6. Git 자동 push
python make_sites_v4.py --git-push

7. 결과
deploys 폴더에 HTML, sitemap.xml, robots.txt, quality_report.csv가 생성됩니다.
