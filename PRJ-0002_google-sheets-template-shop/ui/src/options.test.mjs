import test from 'node:test'
import assert from 'node:assert/strict'
import { buildCommand, fileName, KINDS, JOBS, THEMES } from './options.mjs'

test('명령어 생성', () => {
  assert.equal(buildCommand({ kind: 'budget', job: 'student', theme: 'sage' }),
    'python -m engine.cli --kind budget --job student --theme sage --out output')
})
test('잘못된 값 거부 (명령어 끼워넣기 포함)', () => {
  assert.throws(() => buildCommand({ kind: 'x', job: 'student', theme: 'sage' }))
  assert.throws(() => buildCommand({ kind: 'budget', job: 'student; rm -rf /', theme: 'sage' }))
  assert.throws(() => buildCommand({ kind: 'budget', job: 'student', theme: 'red' }))
})
test('모든 조합 파일명', () => {
  for (const k in KINDS) for (const j in JOBS) for (const t in THEMES)
    assert.ok(fileName({ kind: k, job: j, theme: t }).endsWith('.xlsx'))
})
