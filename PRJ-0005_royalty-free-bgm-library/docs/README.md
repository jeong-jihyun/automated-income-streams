# 설계 요약 (PRJ-0005)
설계 문서 원본: https://docs.google.com/document/d/1YnXQ8LJeJgknQbL__8jp9w09vOVwi9L3s6P6K6eUk10/edit

- 스택: Python + ffmpeg + 정적 HTML (서버 비용 거의 없음)
- 프로그램이 맡는 일: 곡 정보 검증, 미리듣기, 카탈로그 사이트, 라이선스 안내문 초안
- 맡지 않는 일: 작곡, 결제 구현, 외부 마켓 자동 등록, Content ID 등록
- 핵심 안전장치: 곡마다 제작 방법과 권리 근거를 기록하지 않으면 사이트를 만들지 않음
