import json, os
HERE = os.path.dirname(os.path.dirname(__file__))


def load_specs(path=None):
    with open(path or os.path.join(HERE, "config", "specs.json"), encoding="utf-8") as f:
        return json.load(f)
