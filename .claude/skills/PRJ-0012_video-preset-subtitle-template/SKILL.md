---
name: video-preset-subtitle-template
description: 자막 스타일 설정 JSON을 점검하고 ASS/SRT 자막, ffmpeg 미리보기, 글꼴 라이선스 목록, 구매자 안내 PDF, 판매용 ZIP, 상품 설명 초안을 만드는 명령줄 도구. 사용자가 영상 자막 템플릿 판매 준비를 요청할 때 사용.
---

# 자막 스타일 묶음 빌더

1. 스타일 설정 JSON(`sample/styles.json` 형식)을 확인한다.
2. `python -m video_preset check --config <json>` 로 점검하고 문제를 쉬운 말로 설명한다.
3. 통과하면 `build --config <json> --out <결과>` 를 실행한다.
4. 프리미어·캡컷에서 열리는지는 확인하지 못했다고 알리고, 사람이 앱에서 직접 열어 보게 한다.
5. 글꼴 라이선스와 마켓 규정은 사람이 확인한다. 마켓 등록은 사람이 직접 한다.
