import json
import os

_P = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "presets.json")
with open(_P, encoding="utf-8") as f:
    PRESETS = json.load(f)
KINDS = ("budget", "project", "inventory")


def check(kind, job, theme):
    if kind not in KINDS:
        raise ValueError(f"kind는 {KINDS} 중 하나")
    if job not in PRESETS["jobs"]:
        raise ValueError(f"job은 {list(PRESETS['jobs'])} 중 하나")
    if theme not in PRESETS["themes"]:
        raise ValueError(f"theme은 {list(PRESETS['themes'])} 중 하나")
