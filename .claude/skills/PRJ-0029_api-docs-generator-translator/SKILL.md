---
name: api-docs-generator-translator
description: 파이썬 코드나 OpenAPI JSON에서 영어·한글 API 문서를 만들고 번역 목록(낡음 표시, 용어집)을 관리하는 명령줄 도구. 사용자가 API 문서 자동 생성·번역 도구 개발을 요청할 때 사용.
---
# API 문서 자동 생성·번역
`python -m apidocs build <소스> --out <폴더> [--catalog translations.json] [--glossary g.json]`
번역은 사람이 `ko` 칸을 채운다. 자동 번역은 하지 않는다. 한계는 README 참고.
