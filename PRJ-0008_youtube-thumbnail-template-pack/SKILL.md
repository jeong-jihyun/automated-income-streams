---
name: thumbnail-pack-builder
description: 썸네일·채널아트 PNG 폴더의 규격을 점검하고 미리보기 모음 이미지, 구매자 안내 PDF, 상품 설명 초안을 만드는 명령줄 도구. 사용자가 유튜브 템플릿 묶음 판매 준비를 요청할 때 사용.
---

# 썸네일 묶음 빌더

1. PNG 폴더와 `pack.json`(묶음 이름, 테마, 템플릿 링크) 경로를 확인한다.
2. `python -m thumb_pack check --input <폴더>` 로 점검하고 불합격 사유를 쉬운 말로 설명한다.
3. 합격하면 `build --input <폴더> --config <pack.json> --out <결과>` 를 실행한다.
4. 규격은 예시값, Canva 판매 규정은 사람이 확인해야 한다고 안내한다.
5. Canva·Gumroad 등록은 사람이 직접 한다. 자동 등록하지 않는다.
