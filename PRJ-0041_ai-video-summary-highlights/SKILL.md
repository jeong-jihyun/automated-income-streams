---
name: ai-video-summary-highlights
description: 자막(SRT/VTT)으로 영상 요약, 구간별 목차, 하이라이트 구간을 만들고 ffmpeg로 하이라이트 영상을 잘라 내는 도구(영상 내용은 분석하지 않음). 사용자가 AI 영상 요약·하이라이트 서비스 개발을 요청할 때 사용.
---
# PRJ-0041 AI 영상 요약·하이라이트 서비스 (자막 기반 엔진)
`python -m vidsum <자막> --out out [--video 영상.mp4] [--highlights 3]`. 한계는 README 참고.
