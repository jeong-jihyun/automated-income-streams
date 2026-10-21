---
name: kr-commerce-api-gateway
description: 네이버·쿠팡·카카오 주문 응답을 공통 주문 형식으로 바꾸고 API 키·호출 제한·사용량·캐시를 갖춘 게이트웨이 뼈대(가짜 응답 시험 서버 포함). 사용자가 국내 커머스 API 통합 중개 개발을 요청할 때 사용.
---
`python -m kr_gateway check|serve --mappings ... --keys ...`. 실제 API 필드·인증은 문서로 확인해 매핑과 fetcher를 채워야 함.
