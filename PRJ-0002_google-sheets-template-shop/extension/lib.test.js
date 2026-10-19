const test = require('node:test'), assert = require('node:assert/strict')
const { parseListing, tagLine } = require('./lib.js')
test('정상 문구', () => {
  const l = parseListing(JSON.stringify({ title: ' 가계부 ', description: '설명', tags: ['a', 'b'] }))
  assert.equal(l.title, '가계부'); assert.equal(tagLine(l), 'a, b')
})
test('잘못된 입력 거부', () => {
  assert.throws(() => parseListing('{'))
  assert.throws(() => parseListing(JSON.stringify({ title: '', description: 'x', tags: [] })))
  assert.throws(() => parseListing(JSON.stringify({ title: 'a', description: 'x', tags: 'a' })))
})
