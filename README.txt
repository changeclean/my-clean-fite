V5 원클릭 배포 업데이트

압축 안의 파일:
- keyword_engine_v5.py
- deploy.py

설치:
두 파일을 기존 V5 프로젝트 폴더에 넣으세요.

중요:
기존 index.html은 template.html로 이름 변경되어 있어야 합니다.
home_template.html도 같은 폴더에 있어야 합니다.

기본 실행:
python deploy.py

테스트 실행:
python deploy.py --limit 100 --no-git

기존 키워드만 사용:
python deploy.py --skip-keywords

전체 재생성:
python deploy.py --force

네이버/구글 등록 전 확인:
https://changeclean1.netlify.app/
https://changeclean1.netlify.app/sitemap.xml
https://changeclean1.netlify.app/robots.txt
