# NanumGothic.ttf 넣는 방법

저장소에는 폰트 파일(4.6MB)이 들어 있지 않습니다. 아래 중 하나로 `engine/fonts/NanumGothic.ttf` 를 만들어 주세요.

1. (가장 쉬움) 채팅으로 받은 `PRJ-0001-goodnotes-planner.zip` 에는 이미 들어 있습니다.
2. 파이썬으로 내려받기:
```bash
pip download --no-deps koreanize-matplotlib
unzip koreanize_matplotlib-*.whl 'koreanize_matplotlib/fonts/NanumGothic.ttf'
cp koreanize_matplotlib/fonts/NanumGothic.ttf engine/fonts/
```
3. 네이버 한글한글아름답게 사이트(hangeul.naver.com)에서 나눔고딕을 내려받아 같은 이름으로 복사.

폰트가 없으면 한글이 PDF에 나오지 않습니다. 영어(`--lang en`)는 기본 폰트로도 만들어집니다.
