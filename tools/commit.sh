#!/bin/bash
# usage: commit.sh N FOLDER "항목명" "README 표 상태"
set -e
N=$1; F=$2; T=$3; ST=$4
cd "$(dirname "$0")/.."
SKILLDIR=.claude/skills/$F
mkdir -p $F/claude $SKILLDIR
cp $F/CLAUDE.md $F/claude/CLAUDE.md
cp $F/SKILL.md $SKILLDIR/SKILL.md
python3 - "$N" "$F" "$T" "$ST" <<'PY'
import sys
n,f,t,st=sys.argv[1:5]
s=open("README.md",encoding="utf-8").read()
row=f"| PRJ-{n} | {t} | [{f}]({f}) | {st} |\n"
if f"| PRJ-{n} |" not in s:
    if not s.endswith("\n"): s+="\n"
    open("README.md","w",encoding="utf-8").write(s+row)
PY
find $F -name __pycache__ -prune -exec rm -rf {} \; 2>/dev/null || true
rm -rf $F/.pytest_cache
git add $F $SKILLDIR README.md
git commit -q -m "Add PRJ-$N $T

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01YMRk9vmwYpz1d27oFR3EH3"
git pull -q --rebase origin main
git push origin HEAD:main 2>&1 | tail -1
git log --oneline | head -1
