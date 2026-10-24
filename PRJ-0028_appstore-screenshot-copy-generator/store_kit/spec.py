"""스토어 규격(알려진 값). 정책·규격은 바뀔 수 있으므로 등록 전에 애플·구글 공식 안내로 확인해야 한다."""
SIZES = {                      # 이름: (가로, 세로)
    "ios_6.7": (1290, 2796),
    "ios_6.5": (1242, 2688),
    "ios_5.5": (1242, 2208),
    "play_phone": (1080, 1920),
}
LIMITS = {                     # 글자 수 제한(알려진 값)
    "app_store": {"title": 30, "subtitle": 30, "keywords": 100, "description": 4000, "promo": 170},
    "play": {"title": 30, "short": 80, "full": 4000},
}
RISKY_CLAIMS = ["1위", "최고의", "100% 무료", "공식 인증", "No.1", "#1", "best", "무조건", "완벽한"]
SCREENSHOT_LIMIT = {"app_store": (1, 10), "play": (2, 8)}
