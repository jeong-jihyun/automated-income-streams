# 설계 요약
기준 재고(SQLite) → sale(멱등·원자 차감) → sync_sku(채널별 pusher, 변경분만) → reconcile.
설계 문서: https://docs.google.com/document/d/1hX-Dj4EbDo-NZlFuWyTep6WOjzleNVbDJ19Fjsm-TEA
