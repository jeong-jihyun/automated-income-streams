---
name: language-audiobook-builder
description: 회화 문장표 CSV를 점검하고 문장별 음성과 무음 간격을 합친 챕터 mp3, 목차, 교재 PDF, 상품 설명 초안을 만드는 명령줄 도구 (ffmpeg 사용). 사용자가 회화 오디오북 제작을 요청할 때 사용.
---

# 회화 오디오북 빌더

1. 문장표 CSV(`sample/sentences.csv` 형식)를 확인한다.
2. `python -m audiobook_builder check --sheet <csv>` 로 점검하고 문제를 쉬운 말로 설명한다.
3. 통과하면 `build --sheet <csv> --out <결과> --provider <silent|folder|edge-tts>` 를 실행한다.
4. silent 는 시험용, edge-tts 는 상업 이용 약관 확인이 필요하다고 알린다.
5. 발음·번역 품질은 사람이 검수한다. 윌라·크몽 등록은 사람이 직접 한다.
