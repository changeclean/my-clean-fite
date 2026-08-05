V8 설치 및 실행
================

1. 아래 두 파일을 기존 정상 Git 저장소 루트에 넣습니다.

C:\Users\USER\Documents\GitHub\my-clean-fite\V8.py
C:\Users\USER\Documents\GitHub\my-clean-fite\v8_page_template.html

기존 구조는 그대로 둡니다.

my-clean-fite
├─ .git
├─ index.html                 기존 정상 메인
├─ images                     기존 이미지 폴더
├─ 기존 상세페이지 폴더 3천여 개
├─ sitemap.xml
├─ rss.xml
├─ robots.txt
├─ V8.py
└─ v8_page_template.html

2. 먼저 10개만 Git 없이 테스트합니다.

cd "C:\Users\USER\Documents\GitHub\my-clean-fite"
python .\V8.py --count 10 --no-git

3. 정상 출력 기준

신규 생성 완료: 10개
품질검사 PASS: 10개
품질검사 CHECK: 0개
루트 index.html 보존 확인: 정상

4. 테스트 폴더 하나를 브라우저로 확인합니다.

생성된 폴더 이름은 v8_keywords_added.csv에 기록됩니다.
해당 폴더의 index.html을 더블클릭해 디자인과 이미지 순서를 확인합니다.

5. 테스트로 만든 10개도 정상 페이지이므로 그대로 둔 상태에서
나머지 2,990개를 생성하려면:

python .\V8.py --count 2990

처음부터 바로 3,000개를 만들려면:

python .\V8.py

주의
----
- V8은 기존 index.html을 수정하지 않습니다.
- 기존 페이지 폴더가 존재하면 덮어쓰지 않습니다.
- 현재 Git 브랜치를 자동 감지해 origin으로 push합니다.
- Netlify가 main 브랜치를 사용 중이라면 현재 Git도 main이어야 합니다.
- netlify.toml을 새로 만들 필요가 없습니다. 기존 정상 설정을 유지하세요.
