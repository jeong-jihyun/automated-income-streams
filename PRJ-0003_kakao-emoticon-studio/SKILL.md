---
name: kakao-emoticon-checker
description: 이모티콘 그림 폴더의 규격(크기·개수·형식·용량·투명 배경)을 검사하고, 크기 맞춤, 순번 이름 정리, 구성표 CSV, 제안 문구 초안을 만들어 주는 명령줄 도구. 사용자가 카카오 이모티콘 규격 검수 도구 관련 파일 검수·정리를 요청할 때 사용.
---

# 카카오 이모티콘 규격 검수 도구

1. 사용자의 폴더 경로를 확인한다.
2. `python -m kakao_checker` 로 실행하고 결과(통과/문제 목록)를 쉬운 한국어로 설명한다.
3. 규격 숫자는 설정 JSON 값이 예시임을 알리고 공식 안내 확인을 권한다.
4. 마켓/플랫폼에 자동 등록하지 않는다. 제출·업로드는 사람이 직접 한다.

사용 예:
```
python -m kakao_checker check ./내그림폴더
python -m kakao_checker resize ./내그림폴더 ./맞춤결과
python -m kakao_checker rename ./내그림폴더 --prefix mychar # 미리보기
python -m kakao_checker rename ./내그림폴더 --prefix mychar --apply # 실제 변경
python -m kakao_checker plan --count 32 > 구성표.csv
python -m kakao_checker draft "하루" "졸린 곰" "느긋함"
```
