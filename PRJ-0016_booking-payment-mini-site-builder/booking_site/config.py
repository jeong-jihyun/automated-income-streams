import json
import re

TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ConfigError(ValueError):
    pass


def to_min(t):
    h, m = t.split(":"); return int(h) * 60 + int(m)


def load(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON 형식 오류: {e}")
    errs = []
    for k in ("shop_name", "open", "close", "slot_minutes", "services", "refund_policy"):
        if k not in cfg: errs.append(f"'{k}' 항목이 없습니다")
    if errs: raise ConfigError("; ".join(errs))
    for k in ("open", "close"):
        if not TIME.match(str(cfg[k])): errs.append(f"{k}는 HH:MM 형식이어야 합니다")
    if not errs and to_min(cfg["open"]) >= to_min(cfg["close"]): errs.append("close가 open보다 늦어야 합니다")
    if not isinstance(cfg["slot_minutes"], int) or cfg["slot_minutes"] <= 0: errs.append("slot_minutes는 1 이상의 정수")
    if not cfg["services"]: errs.append("서비스가 하나도 없습니다")
    ids = [s.get("id") for s in cfg["services"]]
    if len(set(ids)) != len(ids): errs.append("서비스 id가 중복입니다")
    for s in cfg["services"]:
        if not isinstance(s.get("price"), int) or s["price"] < 0: errs.append(f"서비스 {s.get('id')} 가격이 올바르지 않습니다")
    pol = cfg["refund_policy"]
    if not pol or not any(p.get("hours_before") == 0 for p in pol): errs.append("환불 규정에 hours_before 0 단계가 필요합니다")
    for p in pol:
        if not 0 <= p.get("percent", -1) <= 100: errs.append("환불 비율은 0~100")
    if errs: raise ConfigError("; ".join(errs))
    return cfg
