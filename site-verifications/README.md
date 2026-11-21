# 체인지클린 V2: 네이버·구글 소유권 확인 HTML

등록할 사이트: https://changeclean-v2-store.netlify.app/

## 첫 단계: 서비스에서 발급한 파일 받기
1. [네이버 서치어드바이저](https://searchadvisor.naver.com/) → 웹마스터 도구 → 사이트 추가 → https://changeclean-v2-store.netlify.app/ → 'HTML 파일 업로드' 선택 → 인증 파일 다운로드.
2. [구글 서치콘솔](https://search.google.com/search-console) → 속성 추가 → **URL 접두어** → https://changeclean-v2-store.netlify.app/ → 'HTML 파일' 방법 선택 → 인증 파일 다운로드.
3. 받은 두 파일을 **원본 이름, 원본 내용 그대로** 이 폴더(site-verifications)에 추가합니다. 예: naver...html, google...html. 다운로드 과정에서 파일명 뒤에 (1)이 붙었다면 발급 페이지에서 정확한 요구 파일명을 확인하세요.

## 배포 동작
- Netlify는 GitHub의 `v2-restore-2026-09-15` 브랜치를 빌드합니다.
- `netlify.toml`: `node v2-build-100.cjs`, 출력 폴더 `v2-dist`.
- 빌드 스크립트는 site-verifications에 있는 `naver*.html`, `google*.html` 파일을 자동으로 출력 폴더 최상위에 복사합니다. 이 README는 복사하지 않습니다.
- 배포 완료 후 `https://changeclean-v2-store.netlify.app/<다운받은_파일명>.html`을 브라우저에서 열어 파일 원본이 표시되는지 확인한 다음 인증 버튼을 누릅니다.
- **기존 운영 사이트 소유확인 파일은 새 Netlify 사이트 인증에 재사용하지 마세요.** 새로운 사이트에서 발급한 검증 파일을 사용하세요.

## 현재 검증 및 색인 상태
- 홈(/)과 100개 지역 페이지(/area/...)를 준비했습니다.
- sitemap: https://changeclean-v2-store.netlify.app/sitemap.xml (홈 + 100개 지역 = 101개 URL)
- robots.txt: https://changeclean-v2-store.netlify.app/robots.txt
- 현재 빌드 결과물 `_headers`에 사이트 전체 `X-Robots-Tag: noindex, nofollow, noarchive`를 유지합니다. 이는 미리보기 중복 색인을 방지하기 위한 의도적인 설정입니다.
- **소유확인 = 사이트 공개/색인 허용이 아닙니다.** 소유권 확인을 먼저 마치고 실제 게시 여부, 고객 후기 진위 및 중복 콘텐츠·URL 이전 전략을 확인한 후에 색인 차단을 해제하세요.
- 사이트맵 제출과 수집 요청은 색인 차단을 해제한 이후 진행합니다. 차단된 상태에서 제출하면 색인 제외(noindex)로 나올 수 있습니다.
- Netlify 최신 배포가 정상 게시(Published) 상태인지 확인해야 하며, GitHub 수정만으로 외부 배포 완료라고 간주하지 않습니다.
