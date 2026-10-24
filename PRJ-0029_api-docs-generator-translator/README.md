# PRJ-0029 API 문서 자동 생성·번역 도구

파이썬 코드(독스트링)나 OpenAPI JSON에서 영어 문서(`docs_en.md`)와 한글 문서(`docs_ko.md`)를 만들고, 번역 목록(`translations.json`)을 관리하는 명령줄 도구입니다.

## 쓰는 법
```
python -m apidocs build sample/shop_api.py --out out --catalog translations.json --glossary sample/glossary.json
python -m apidocs build sample/openapi.json --out out --catalog translations.json
```
1. 처음 실행하면 번역 목록에 "번역 필요" 문장이 쌓입니다(용어집이 있으면 `hint`에 용어 표기 힌트).
2. `translations.json`의 빈 `ko` 칸을 사람이 채우고 `status`를 "번역됨"으로 바꿉니다.
3. 다시 실행하면 한글 문서에 반영됩니다. 빈 칸은 원문 + *(번역 필요)* 로 표시됩니다.
4. 원문이 바뀌면 옛 번역은 "사용 안 함"이 되고 새 문장이 "번역 필요"로 추가됩니다(원문이 돌아오면 복구).

## 안전
- 파이썬 코드는 `ast`로 읽기만 하고 **실행하지 않습니다**. `_`로 시작하는 이름은 제외합니다.
- 자동 번역은 하지 않습니다. 코드에서 `translate.fill(catalog, 함수)`로 번역 함수를 꽂으면 "번역됨(자동, 검수 필요)"로 표시됩니다.

## 확인한 것 (테스트 8개 통과)
시그니처 추출, 비공개 제외, 코드 미실행, OpenAPI 표 렌더링, 번역 목록 동기화·낡음 처리, 한글 문서 반영, 용어집, CLI 왕복, 오류 코드.

## 확인하지 못한 것
- 실제 번역 품질(자동 번역 연결은 시험하지 않음), 큰 프로젝트·여러 파일 일괄 처리
- OpenAPI YAML·`$ref`·요청 본문 스키마·3.1 일부 기능, 다른 언어(JS/Java 등) 코드
- GitHub Marketplace 등록·결제·배포 (등록은 직접 해야 함)
