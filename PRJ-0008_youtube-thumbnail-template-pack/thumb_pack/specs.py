import json, os
HERE = os.path.dirname(os.path.dirname(__file__))


def load_specs(path=None):
    with open(path or os.path.join(HERE, "config", "specs.json"), encoding="utf-8") as f:
        return json.load(f)


def load_pack(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"묶음 설정 파일이 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        pack = json.load(f)
    for k in ("pack_name", "theme", "items"):
        if k not in pack:
            raise ValueError(f"묶음 설정에 '{k}' 가 없습니다")
    if not pack["items"]:
        raise ValueError("묶음 설정의 items 가 비어 있습니다")
    return pack
