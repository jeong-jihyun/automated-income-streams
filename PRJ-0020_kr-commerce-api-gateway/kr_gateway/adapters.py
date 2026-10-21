"""채널별 응답을 공통 주문 형식으로 바꾼다. 필드 이름은 매핑 파일(JSON)에서 읽으므로 실제 API에 맞게 고칠 수 있다."""
import json

UNIFIED_STATUS = {"paid", "shipping", "delivered", "cancelled", "unknown"}


class AdapterError(ValueError):
    pass


def dig(obj, path):
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def load_mappings(path):
    try:
        m = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise AdapterError(f"매핑 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise AdapterError(f"JSON 형식 오류: {e}")
    m = {k: v for k, v in m.items() if not k.startswith("_")}
    for ch, spec in m.items():
        for k in ("orders_path", "id", "status", "amount", "ordered_at", "status_map"):
            if k not in spec:
                raise AdapterError(f"{ch}: '{k}' 매핑이 없습니다")
        bad = set(spec["status_map"].values()) - UNIFIED_STATUS
        if bad:
            raise AdapterError(f"{ch}: 알 수 없는 공통 상태 {sorted(bad)}")
    return m


def normalize(channel, payload, spec):
    items = dig(payload, spec["orders_path"])
    if items is None:
        raise AdapterError(f"{channel}: 응답에서 '{spec['orders_path']}' 를 찾지 못했습니다 (응답 형식이 바뀌었을 수 있습니다)")
    if not isinstance(items, list):
        raise AdapterError(f"{channel}: 주문 목록이 배열이 아닙니다")
    out, skipped = [], 0
    for it in items:
        oid, amount = dig(it, spec["id"]), dig(it, spec["amount"])
        if oid is None or not isinstance(amount, (int, float)) or isinstance(amount, bool):
            skipped += 1
            continue
        out.append({"channel": channel, "order_id": str(oid), "status": spec["status_map"].get(dig(it, spec["status"]), "unknown"),
                    "amount": int(amount), "buyer": dig(it, spec.get("buyer", "")) if spec.get("buyer") else None,
                    "ordered_at": dig(it, spec["ordered_at"])})
    return out, skipped
