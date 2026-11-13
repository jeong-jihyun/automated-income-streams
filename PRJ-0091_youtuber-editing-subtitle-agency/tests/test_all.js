'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');

test('시간 변환 왕복', () => {
  assert.strictEqual(C.parseTime('00:01:02,500'), 62500);
  assert.strictEqual(C.formatTime(3723004), '01:02:03,004');
  assert.strictEqual(C.parseTime('00:00:61,000'), null);
  assert.strictEqual(C.parseTime('abc'), null);
});
test('샘플 SRT 읽기', () => {
  const r = C.parseSrt(C.SAMPLE_SRT);
  assert.strictEqual(r.cues.length, 4);
  assert.strictEqual(r.errors.length, 0);
});
test('빈 글·잘못된 글은 오류', () => {
  assert.ok(C.parseSrt('').errors.length > 0);
  assert.ok(C.parseSrt('1\n엉터리\n글').errors.length > 0);
});
test('겹침·긴 줄·초당 글자 수 판정', () => {
  const r = C.parseSrt(C.SAMPLE_SRT);
  const types = C.checkCues(r.cues, { maxLineChars: 20, maxCps: 12 }).map(i => i.type);
  assert.ok(types.includes('overlap'));
  assert.ok(types.includes('long'));
  assert.ok(types.includes('cps'));
});
test('깨끗한 자막은 문제 없음', () => {
  const r = C.parseSrt('1\n00:00:01,000 --> 00:00:03,000\n안녕하세요\n\n2\n00:00:03,000 --> 00:00:05,000\n반갑습니다');
  assert.strictEqual(C.checkCues(r.cues).length, 0);
});
test('끝이 시작보다 빠르면 표시', () => {
  const r = C.parseSrt('1\n00:00:05,000 --> 00:00:02,000\n가');
  assert.strictEqual(C.checkCues(r.cues)[0].type, 'duration');
});
test('시간 이동과 0초 멈춤', () => {
  const r = C.parseSrt(C.SAMPLE_SRT);
  const s = C.shiftCues(r.cues, 1.5);
  assert.strictEqual(s.cues[0].start, 2500);
  assert.strictEqual(s.cues[0].end - s.cues[0].start, r.cues[0].end - r.cues[0].start);
  const n = C.shiftCues(r.cues, -2);
  assert.strictEqual(n.cues[0].start, 0);
  assert.strictEqual(n.clamped, 1);
});
test('SRT 만들고 다시 읽으면 같다', () => {
  const r = C.parseSrt(C.SAMPLE_SRT);
  const again = C.parseSrt(C.buildSrt(r.cues));
  assert.deepStrictEqual(again.cues.map(c => [c.start, c.end, c.text]), r.cues.map(c => [c.start, c.end, c.text]));
});
test('견적 기본 계산', () => {
  const q = C.quote({ minutes: 10, ratePerMin: 20000, edits: 3, editFee: 10000 });
  assert.strictEqual(q.supply, 230000);
  assert.strictEqual(q.vat, 23000);
  assert.strictEqual(q.total, 253000);
});
test('돈 합계 보존: 항목 합 = 총합 (여러 값)', () => {
  for (let m = 0; m <= 37; m += 0.5) for (const rate of [333, 1001, 20000]) for (const e of [0, 1, 3, 7]) for (const fee of [0, 777, 10000]) {
    const q = C.quote({ minutes: m, ratePerMin: rate, edits: e, editFee: fee });
    assert.strictEqual(q.items.reduce((a, i) => a + i.supply, 0), q.supply);
    assert.strictEqual(q.items.reduce((a, i) => a + i.vat, 0), q.vat);
    assert.strictEqual(q.items.reduce((a, i) => a + i.total, 0), q.total);
    assert.strictEqual(q.supply + q.vat, q.total);
    q.items.forEach(i => assert.ok(Number.isInteger(i.vat) && i.vat >= 0));
  }
});
test('allocate는 합을 정확히 보존', () => {
  const a = C.allocate([1, 1, 1], 10);
  assert.strictEqual(a.reduce((x, y) => x + y, 0), 10);
  assert.deepStrictEqual(C.allocate([0, 0], 5), [0, 0]);
});
test('이상한 입력은 0으로', () => {
  const q = C.quote({ minutes: -5, ratePerMin: 'abc', edits: -1, editFee: null });
  assert.strictEqual(q.total, 0);
});
test('화면 파일: 외부 주소 없음, viewport, core.js 사용', () => {
  const dir = path.join(__dirname, '..', 'app');
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.ok(html.includes('name="viewport"'));
  assert.ok(html.includes('src="core.js"'));
  for (const f of ['index.html', 'core.js', 'style.css']) {
    assert.ok(!/https?:\/\//.test(fs.readFileSync(path.join(dir, f), 'utf8')), f + ' 에 http 주소');
  }
});
