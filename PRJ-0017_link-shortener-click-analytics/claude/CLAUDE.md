# PRJ-0017 작업 규칙
- 한국어, 쉬운 말. 외부 서비스 없이 표준 라이브러리만. 인터넷 공개 운영 기능은 만들지 않고 위험을 README에 적는다.
- 구조: link_short/core.py(검증·집계) server.py cli.py. 주의: LinkError가 ValueError 하위라 except ValueError로 삼키지 말 것.
- 테스트: python -m pytest -q
