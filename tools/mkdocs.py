import sys, json, os
d = json.load(open(sys.argv[1], encoding="utf-8")); os.chdir(d["dir"])
open("README.md", "w", encoding="utf-8").write(f"""# {d['title']}

{d['intro']}

## 쓰는 법
```
{d['usage']}
```

## 지키는 것
{chr(10).join('- ' + x for x in d['rules'])}

## 확인한 것 (테스트 {d['tests']}개 통과)
{d['verified']}

## 확인하지 못한 것
{chr(10).join('- ' + x for x in d['unverified'])}
- 설계 문서(드라이브)는 읽지 않고 시트 한 줄 설명으로 범위를 잡았습니다.
""")
open("CLAUDE.md", "w", encoding="utf-8").write(f"# {d['title'].split(' ')[0]} 규칙\n" + "\n".join("- " + x for x in d["claude"]) + f"\n- 시험: `python -m pytest -q` ({d['tests']}개). 확인 못 한 것은 README에 정직하게 적는다.\n")
open("SKILL.md", "w", encoding="utf-8").write(f"---\nname: {d['slug']}\ndescription: {d['desc']}\n---\n# {d['title']}\n`{d['cmd']}`. 한계는 README 참고.\n")
os.makedirs("docs", exist_ok=True)
open("docs/design.md", "w", encoding="utf-8").write(f"# 설계 요약\n{d['design']}\n설계 문서(드라이브)는 읽지 않고 시트 한 줄 설명으로 범위를 잡았다.\n")
