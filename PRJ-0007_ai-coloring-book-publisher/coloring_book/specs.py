import json, os

HERE = os.path.dirname(os.path.dirname(__file__))


def load_specs(path=None):
    with open(path or os.path.join(HERE, "config", "kdp_specs.json"), encoding="utf-8") as f:
        return json.load(f)


def trim_size(specs, name):
    if name not in specs["trim_sizes_in"]:
        raise ValueError(f"지원하지 않는 책 크기 '{name}'. 선택: {', '.join(specs['trim_sizes_in'])}")
    return tuple(specs["trim_sizes_in"][name])
