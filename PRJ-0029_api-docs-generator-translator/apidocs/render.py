"""문서 항목 → 마크다운. lang='en'이면 원문, 'ko'면 번역(없으면 원문 + '(번역 필요)' 표시)."""
from .translate import lookup

LABEL = {"en": {"func": "Functions", "cls": "Classes", "meth": "Methods", "params": "Parameters", "resp": "Responses", "missing": ""},
         "ko": {"func": "함수", "cls": "클래스", "meth": "메서드", "params": "매개변수", "resp": "응답", "missing": " *(번역 필요)*"}}


def _t(text, lang, catalog):
    text = (text or "").strip()
    if not text or lang == "en": return text
    ko = lookup(catalog, text)
    return ko if ko else text + LABEL["ko"]["missing"]


def render(items, lang="en", catalog=None):
    catalog, L, out = catalog or {}, LABEL[lang], []
    if "ops" in items:
        out.append(f"# {_t(items['title'], lang, catalog)} v{items['version']}\n")
        for o in items["ops"]:
            out.append(f"## `{o['method']} {o['path']}`\n\n{_t(o['summary'], lang, catalog)}\n")
            if o["params"]:
                out.append(f"**{L['params']}**\n\n| name | in | required | type | description |\n|---|---|---|---|---|")
                out += [f"| `{p['name']}` | {p['in']} | {'yes' if p['required'] else 'no'} | {p['type']} | {_t(p['desc'], lang, catalog)} |" for p in o["params"]]
                out.append("")
            out.append(f"**{L['resp']}**\n")
            out += [f"- `{c}`: {_t(d, lang, catalog)}" for c, d in o["responses"].items()]
            out.append("")
    else:
        out.append(f"# {items['module']}\n\n{_t(items['doc'], lang, catalog)}\n")
        if items["functions"]:
            out.append(f"## {L['func']}\n")
            for f in items["functions"]: out.append(f"### `{f['sig']}`\n\n{_t(f['doc'], lang, catalog)}\n")
        if items["classes"]:
            out.append(f"## {L['cls']}\n")
            for c in items["classes"]:
                out.append(f"### `{c['name']}`\n\n{_t(c['doc'], lang, catalog)}\n")
                if c["methods"]:
                    out.append(f"**{L['meth']}**\n")
                    for m in c["methods"]: out.append(f"- `{m['sig']}` — {_t(m['doc'], lang, catalog)}")
                    out.append("")
    return "\n".join(out).rstrip() + "\n"
