# APK 만들기 (휴대폰에서 직접 시험)

- 항목 폴더 안에 `app/index.html`(+ js, css)을 두고 main 에 푸시하면 GitHub Actions 가 APK 를 만들어
  Releases 에 `apk-PRJ-00NN` 이름으로 올립니다.
- 받는 곳: https://github.com/jeong-jihyun/automated-income-streams/releases
- 앱은 인터넷 없이 돌아가는 웹 화면(WebView)입니다. 디버그 서명이라 시험용입니다.
- 설치: 휴대폰 브라우저로 릴리스 페이지 열기 → `.apk` 받기 → 열기 → '출처를 알 수 없는 앱' 허용 → 설치.
- `build_project.py` 로 안드로이드 프로젝트를 만듭니다. 이 작업 환경에서는 구글·메이븐 서버에 접속할 수 없어 직접 빌드할 수 없고, 빌드는 GitHub Actions 에서만 합니다.
