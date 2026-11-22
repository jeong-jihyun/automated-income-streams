# PRJ-0003 카카오 이모티콘 규격 검수 도구 · 모바일 산출물

## 산출물
- `PRJ-0003_UI-설계서_v1.0.docx`
- `PRJ-0003_기능정의서_v1.0.docx`
- `PRJ-0003_API-설계서_v1.0.docx`
- `PRJ-0003_디자인시스템_v1.0.docx`
- `PRJ-0003_모바일-컨셉-디자인-시안.html`

## HTML 실행
압축을 푼 후 `docs/PRJ-0003_모바일-컨셉-디자인-시안.html` 파일을 모바일 또는 데스크톱 브라우저에서 엽니다. 별도 패키지 설치 없이 실행할 수 있습니다.

## 주요 메뉴
1. 홈
2. 작품 이미지 불러오기
3. 규격 검수
4. 이미지 크기 맞춤
5. 파일명 정리
6. 구성표·제안서
7. 설정·도움말

모바일에서는 하단 탭으로 이동하고, 데스크톱에서는 좌측 메뉴를 사용합니다.

## 기존 저장소 기능과 연결 관계
- `kakao_checker.core.check_folder` → 규격 검수
- `kakao_checker.core.resize_all` → 이미지 크기 맞춤
- `kakao_checker.core.rename_files` → 파일명 정리(미리보기/실제 적용 구분)
- `kakao_checker.core.make_plan_table` → 구성표 CSV
- `kakao_checker.core.proposal_draft` → 제안 문구 초안
- `kakao_checker/presets.json` → 규격 프리셋

## 구현 범위 및 주의
이 HTML은 모바일 메뉴 이동, 입력 폼, 브라우저 기본 파일 메타 검사, CSV 다운로드, 제안 문구 생성 등 일부 동작을 포함한 **프론트엔드 컨셉 시안**입니다. 기존 Python Pillow 엔진과 REST API는 연결되어 있지 않습니다. 이미지 변환, 투명 픽셀 최종 판정, 실제 파일명 변경은 서버 연동 후에만 실행할 수 있습니다.

저장소의 `README.md` 및 `presets.json`에 명시된 규격 수치는 예시값입니다. 공식 안내를 확인하고 운영 설정을 갱신해야 합니다. 카카오 로그인·자동 제출·자동 업로드 기능은 범위에 포함하지 않습니다.
