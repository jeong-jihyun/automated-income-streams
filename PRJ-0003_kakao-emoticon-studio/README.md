# 카카오 이모티콘 규격 검수 도구 (PRJ-0003)

이모티콘 그림 폴더의 규격(크기·개수·형식·용량·투명 배경)을 검사하고, 크기 맞춤, 순번 이름 정리, 구성표 CSV, 제안 문구 초안을 만들어 주는 명령줄 도구.

## 준비
pip install pillow pytest

## 사용법
```
python -m kakao_checker check ./내그림폴더
python -m kakao_checker resize ./내그림폴더 ./맞춤결과
python -m kakao_checker rename ./내그림폴더 --prefix mychar # 미리보기
python -m kakao_checker rename ./내그림폴더 --prefix mychar --apply # 실제 변경
python -m kakao_checker plan --count 32 > 구성표.csv
python -m kakao_checker draft "하루" "졸린 곰" "느긋함"
```

## 테스트
`python -m pytest -q`

## 정책 주의
카카오 사이트 로그인·자동 제출·자동 입력 기능은 없습니다. 제출은 사람이 직접 합니다. 규격 숫자는 kakao_checker/presets.json 에 예시값이 들어 있으니 공식 안내를 보고 꼭 고치세요.

## 한계 (솔직하게)
자동 테스트는 프로그램이 만든 더미 파일로만 했습니다. 실제 마켓 심사 통과와 실제 작품 품질은 확인하지 못했습니다.
테스트 10건은 2026-10-20 이 저장소에서 다시 실행해 통과를 확인했습니다. 규격 숫자는 예시이며 공식 안내와 대조하지 않았습니다.
