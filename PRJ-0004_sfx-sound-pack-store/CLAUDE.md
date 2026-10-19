# CLAUDE.md - PRJ-0004 효과음 팩 빌더

- 언어/스택: Python 3 (표준 라이브러리 + ffmpeg), 모듈 `sfx_builder`
- 실행: `python -m sfx_builder ...` 테스트: `python -m pytest -q`
- 규칙: 모든 설명은 한국어, 쉬운 말. 규격 숫자는 JSON 설정 파일에만 둔다(코드에 박지 않음).
- 금지: 플랫폼 자동 로그인·자동 제출·자동 업로드 기능 추가 금지. 원본 파일은 덮어쓰지 않는다.
- AudioJungle/Pond5 로그인·자동 업로드·자동 입력 기능은 없습니다. 업로드는 사람이 직접 합니다. 직접 녹음·제작한 소리만 쓰세요. sfx_builder/settings.json 의 규격 값은 예시이므로 공식 안내를 보고 고치세요.
