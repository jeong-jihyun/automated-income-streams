"""코드·API 명세에서 문서 항목 뽑기. 파이썬은 ast(코드를 실행하지 않고 읽음), API 명세는 OpenAPI JSON."""
import ast
import json


class DocError(ValueError):
    pass


def _sig(fn):
    a = fn.args
    parts, pos = [], a.posonlyargs + a.args
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    for arg, d in zip(pos, defaults):
        s = arg.arg + (f": {ast.unparse(arg.annotation)}" if arg.annotation else "")
        parts.append(s + (f" = {ast.unparse(d)}" if d is not None else ""))
    if a.vararg: parts.append("*" + a.vararg.arg)
    for arg, d in zip(a.kwonlyargs, a.kw_defaults):
        parts.append(arg.arg + (f": {ast.unparse(arg.annotation)}" if arg.annotation else "") + (f" = {ast.unparse(d)}" if d is not None else ""))
    if a.kwarg: parts.append("**" + a.kwarg.arg)
    ret = f" -> {ast.unparse(fn.returns)}" if fn.returns else ""
    return f"{'async ' if isinstance(fn, ast.AsyncFunctionDef) else ''}{fn.name}({', '.join(parts)}){ret}"


def parse_python(source, name="module"):
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise DocError(f"파이썬 문법 오류 {e.lineno}행: {e.msg}")
    items = {"module": name, "doc": ast.get_docstring(tree) or "", "functions": [], "classes": []}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            items["functions"].append({"sig": _sig(node), "doc": ast.get_docstring(node) or ""})
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = [{"sig": _sig(m), "doc": ast.get_docstring(m) or ""} for m in node.body
                       if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_")]
            items["classes"].append({"name": node.name, "doc": ast.get_docstring(node) or "", "methods": methods})
    return items


def parse_openapi(text):
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as e:
        raise DocError(f"JSON 형식 오류: {e}")
    if "paths" not in spec:
        raise DocError("OpenAPI 명세에 paths가 없습니다")
    ops = []
    for path, methods in spec["paths"].items():
        for m, op in methods.items():
            if m.lower() not in ("get", "post", "put", "patch", "delete"): continue
            ops.append({"method": m.upper(), "path": path, "summary": op.get("summary", ""),
                        "params": [{"name": p["name"], "in": p.get("in", ""), "required": bool(p.get("required")), "type": p.get("schema", {}).get("type", ""), "desc": p.get("description", "")} for p in op.get("parameters", [])],
                        "responses": {c: r.get("description", "") for c, r in op.get("responses", {}).items()}})
    return {"title": spec.get("info", {}).get("title", ""), "version": spec.get("info", {}).get("version", ""), "ops": ops}
