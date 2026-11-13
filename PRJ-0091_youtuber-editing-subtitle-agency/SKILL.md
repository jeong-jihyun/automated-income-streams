---
name: youtuber-editing-subtitle-agency
description: SRT 자막 글의 겹침·긴 줄·초당 글자 수를 점검하고 시간 이동을 적용하며, 영상 길이×분당 단가+자막 수정으로 대행 견적(부가세 10%)을 계산하는 휴대폰용 오프라인 웹앱. 자막 점검·편집 대행 견적을 요청할 때 사용.
---
# 사용
- 화면: app/index.html. 계산: app/core.js (`parseSrt`, `checkCues`, `shiftCues`, `buildSrt`, `quote`, `allocate`).
- 시험: `node --test tests/test_all.js`
- 한계: 영상은 분석하지 않고, 기준값(한 줄 20자, 초당 12자)은 입력칸에서 바꾼다.
