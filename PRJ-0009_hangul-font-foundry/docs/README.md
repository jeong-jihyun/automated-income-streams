# 설계 요약 (PRJ-0009)
설계 문서 원본: https://docs.google.com/document/d/1yrwsMwhP0ugxY0HewD80goxx7Olql2sAJvagduVd0oM/edit
- 스택: Python + fontTools + Pillow + reportlab (무료)
- 사람: 콘셉트, 글자 그리기(SVG), 마켓 입점·심사·등록
- 프로그램: 글자 목록, 점검, TTF 빌드, 시험지, 라이선스·설명 초안
- 설계의 '글자 수 20자 통합 테스트'는 그대로 했고, UFO 중간 단계 없이 fontTools로 바로 TTF를 만듦


## 모바일 설계 산출물 추가 (2026-11-22)

- [모바일 UI 설계서](01_UI-설계서.md)
- [기능정의서](02_기능정의서.md)
- [API 설계서](03_API-설계서.md)
- [디자인 시스템](04_디자인시스템.md)
- [모바일 HTML 프로토타입](05_mobile-prototype.html)

HTML 시안은 탭 전환, 글리프 검색/필터, 설정 입력 및 데모 액션을 포함합니다. 검수·TTF 빌드 버튼은 백엔드 API가 연결되기 전의 데모이므로 실제 빌드 성공을 표시하지 않습니다.
