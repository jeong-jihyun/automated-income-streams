---
name: livecommerce-clip-editing-service
description: 방송 자막에서 상품 홍보용 15~45초 구간을 골라 ffmpeg로 클립(세로 변환 가능)과 자막을 만드는 도구(영상 분석 없음, 업로드 없음). 사용자가 라이브커머스 클립 제작 도구 개발을 요청할 때 사용.
---
# PRJ-0060 라이브커머스 클립 영상 제작 대행 (클립 구간 선정·절단 도구)
`python -m clipcut <자막.srt> --video <영상> --keywords 키워드,키워드 --top N [--vertical] --out 폴더`. 한계는 README 참고.
