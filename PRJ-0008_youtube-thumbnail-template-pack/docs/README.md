# PRJ-0008 모바일 컨셉 산출물

- UI 설계서 / 기능정의서 / API 설계서 / 디자인 시스템: DOCX
- `mobile-concept.html`: 모바일 우선 단일 HTML 프로토타입

## 실행
`mobile-concept.html`을 Chrome 또는 Edge에서 열거나 모바일 기기로 전달해 브라우저에서 엽니다. 서버/빌드 도구가 필요 없습니다.

## 구현된 시안 동작
- 하단 5개 탭 이동(홈/묶음/검사/결과/설정)
- 묶음 생성·편집 및 localStorage 메타데이터 저장
- 템플릿 링크/글꼴 입력 폼
- PNG/JPG 다중 파일 선택, 파일명·형식·픽셀 크기·용량 검사
- 불합격 파일이 있으면 결과 생성 차단
- 컨택트시트 PNG 다운로드, 상품 설명 TXT 복사/다운로드
- 구매자 안내서 인쇄 및 PDF 저장 대화상자

## 기존 저장소와의 정합성
기존 PRJ-0008 README 및 `thumb_pack/{checker,preview,guide_pdf,listing,cli}.py`, `config/specs.json`을 기준으로 화면/검사 규칙을 맞췄습니다. 기본 규격은 저장소가 명시한 **예시값**이며 공식 규격으로 단정하지 않습니다.

## 중요한 구현 경계
현재 GitHub 프로젝트는 Python CLI이며 HTTP API 서버가 아닙니다. 동봉 API 설계서는 모바일 UI와 기존 Python 엔진을 연결하기 위한 신규 REST API 제안입니다. HTML은 브라우저에서 동작하는 컨셉 시안으로, Python CLI와 동일한 PDF 렌더링/파일 처리 엔진이 아닙니다. 실제 서비스 연결은 API 서버 구현이 필요합니다.

Canva/Gumroad 로그인, 상품 자동 등록, 가격 결정, 판매 성과 보장 기능은 포함하지 않습니다. YouTube·Google 공식 상품이 아니라는 고지를 유지합니다.
