"""API 키 확인, 분당 호출 제한, 사용량 집계, 짧은 캐시, 채널 호출 묶기. 시계와 채널 호출 함수는 바깥에서 넣는다(시험하기 쉽게)."""
import json
from collections import defaultdict
from . import adapters


class GatewayError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg); self.code = code


class Gateway:
    def __init__(self, keys, mappings, fetchers, clock, cache_sec=30):
        self.keys, self.maps, self.fetchers, self.clock, self.cache_sec = keys, mappings, fetchers, clock, cache_sec
        self.calls = defaultdict(list)      # key → 최근 호출 시각
        self.usage = defaultdict(int)       # key → 과금 대상(성공) 호출 수
        self.cache = {}

    def _auth(self, key):
        if key not in self.keys:
            raise GatewayError(401, "API 키가 올바르지 않습니다")
        now, window = self.clock(), [t for t in self.calls[key] if self.clock() - t < 60]
        if len(window) >= self.keys[key]["rate_per_min"]:
            self.calls[key] = window
            raise GatewayError(429, "분당 호출 한도를 넘었습니다")
        window.append(now); self.calls[key] = window

    def orders(self, key, channels=None):
        self._auth(key)
        wanted = channels or list(self.maps)
        unknown = [c for c in wanted if c not in self.maps]
        if unknown:
            raise GatewayError(400, f"지원하지 않는 채널: {', '.join(unknown)}")
        result, errors, skipped = [], {}, 0
        for ch in wanted:
            hit = self.cache.get(ch)
            if hit and self.clock() - hit[0] < self.cache_sec:
                data = hit[1]
            else:
                try:
                    data = self.fetchers[ch]()
                    self.cache[ch] = (self.clock(), data)
                except Exception as e:      # 한 채널이 죽어도 나머지는 돌려준다
                    errors[ch] = f"채널 호출 실패: {e}"
                    continue
            try:
                items, sk = adapters.normalize(ch, data, self.maps[ch]); result += items; skipped += sk
            except adapters.AdapterError as e:
                errors[ch] = str(e)
        if result or not errors:
            self.usage[key] += 1
        result.sort(key=lambda o: (o["ordered_at"] or "", o["channel"], o["order_id"]), reverse=True)
        return {"orders": result, "errors": errors, "skipped": skipped}
