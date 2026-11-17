'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');

const TODAY = '2026-11-17';
const K = C.makeKey('ACME', 2026, 1);
const chk = (expiry, used = 5, allowed = 10, key = K) => C.checkLicense({ key, expiry, seatsAllowed: allowed, seatsUsed: used, today: TODAY });

test('날짜 읽기: 잘못된 날짜는 null', () => {
  assert.strictEqual(C.parseDate('2026-02-30'), null);
  assert.strictEqual(C.parseDate('2026-13-01'), null);
  assert.strictEqual(C.parseDate('abc'), null);
  assert.strictEqual(C.formatDate(C.parseDate('2024-02-29')), '2024-02-29');
});
test('달 더하기는 말일에 맞춘다', () => {
  assert.strictEqual(C.formatDate(C.addMonths(C.parseDate('2026-01-31'), 1)), '2026-02-28');
  assert.strictEqual(C.formatDate(C.addMonths(C.parseDate('2024-02-29'), 12)), '2025-02-28');
});
test('키 만들기·읽기 왕복, 검사값 규칙', () => {
  assert.match(K, /^ACME-2026-0001-\d{4}$/);
  assert.strictEqual(C.parseKey(K).ok, true);
  assert.strictEqual(C.keyChecksum('AB', '2026', '0001'), String(('AB2026' + '0001').split('').reduce((a, c) => a + c.charCodeAt(0), 0) % 10000).padStart(4, '0'));
});
test('형식 오류: 소문자, 자리수, 검사값 불일치', () => {
  assert.strictEqual(chk('2026-12-31', 5, 10, 'acme-2026-0001-0000').status, 'format');
  assert.strictEqual(chk('2026-12-31', 5, 10, 'ACME-2026-001-1234').status, 'format');
  assert.strictEqual(chk('2026-12-31', 5, 10, '').status, 'format');
  const bad = K.slice(0, -1) + (K.endsWith('0') ? '1' : '0');
  const r = chk('2026-12-31', 5, 10, bad);
  assert.strictEqual(r.status, 'format');
  assert.ok(r.message.includes('검사값'));
});
test('경계: 만료 당일은 만료 임박(아직 유효), 다음날은 만료', () => {
  assert.strictEqual(chk('2026-11-17').status, 'soon');
  assert.strictEqual(chk('2026-11-17').daysLeft, 0);
  assert.strictEqual(chk('2026-11-16').status, 'expired');
  assert.strictEqual(chk('2026-11-16').daysLeft, -1);
});
test('경계: 30일째는 임박, 31일째는 유효', () => {
  assert.strictEqual(chk('2026-12-17').daysLeft, 30);
  assert.strictEqual(chk('2026-12-17').status, 'soon');
  assert.strictEqual(chk('2026-12-18').daysLeft, 31);
  assert.strictEqual(chk('2026-12-18').status, 'valid');
});
test('좌석: 같으면 유효, 하나 넘으면 초과, 만료가 초과보다 우선', () => {
  assert.strictEqual(chk('2027-06-30', 10, 10).status, 'valid');
  assert.strictEqual(chk('2027-06-30', 11, 10).status, 'seats');
  assert.strictEqual(chk('2026-01-01', 11, 10).status, 'expired');
  assert.strictEqual(chk('2026-12-01', 11, 10).status, 'seats');
});
test('입력 오류: 날짜·좌석', () => {
  assert.strictEqual(chk('2026-02-30').status, 'input');
  assert.strictEqual(chk('2026-12-31', -1, 10).status, 'input');
  assert.strictEqual(chk('2026-12-31', 1.5, 10).status, 'input');
  assert.strictEqual(C.checkLicense({ key: K, expiry: '2026-12-31', seatsAllowed: 1, seatsUsed: 1, today: 'x' }).status, 'input');
});
test('샘플 화면 값은 만료 임박으로 나온다', () => {
  const r = C.checkLicense({ key: C.SAMPLE_KEY, expiry: '2026-12-10', seatsAllowed: 20, seatsUsed: 18, today: C.SAMPLE_TODAY });
  assert.strictEqual(r.status, 'soon');
  assert.strictEqual(r.daysLeft, 23);
});
test('견적: 구간 누진 단가(1년, 기본 지원)', () => {
  const q = C.quote({ seats: 10, years: 1, support: 'basic' });
  assert.strictEqual(q.supply, 1200000);
  assert.strictEqual(q.vat, 120000);
  assert.strictEqual(q.total, 1320000);
  const q2 = C.quote({ seats: 60, years: 1, support: 'basic' });
  assert.strictEqual(q2.perYearLicense, 10 * 120000 + 40 * 100000 + 10 * 80000);
});
test('견적: 지원 추가금과 다년 할인', () => {
  const q = C.quote({ seats: 10, years: 3, support: 'premium' });
  assert.strictEqual(q.gross, 3 * (1200000 + 1800000));
  assert.strictEqual(q.discount, 900000);
  assert.strictEqual(q.supply, 8100000);
  assert.strictEqual(q.total, 8910000);
});
test('견적: 잘못된 입력은 오류', () => {
  assert.ok(C.quote({ seats: 0, years: 1, support: 'basic' }).error);
  assert.ok(C.quote({ seats: 5, years: 4, support: 'basic' }).error);
  assert.ok(C.quote({ seats: 5, years: 1, support: 'x' }).error);
});
test('돈 합계 보존: 항목 합 = 총합 (여러 값)', () => {
  for (let seats = 1; seats <= 120; seats += 1) for (const years of [1, 2, 3]) for (const support of Object.keys(C.SUPPORT)) {
    const q = C.quote({ seats, years, support });
    assert.strictEqual(q.items.reduce((a, i) => a + i.supply, 0), q.supply);
    assert.strictEqual(q.items.reduce((a, i) => a + i.vat, 0), q.vat);
    assert.strictEqual(q.items.reduce((a, i) => a + i.total, 0), q.total);
    assert.strictEqual(q.supply + q.vat, q.total);
    assert.strictEqual(q.gross - q.discount, q.supply);
    q.items.forEach(i => assert.ok(Number.isInteger(i.vat) && i.vat >= 0 && Number.isInteger(i.supply) && i.supply >= 0));
  }
});
test('allocate는 합을 정확히 보존', () => {
  assert.strictEqual(C.allocate([1, 1, 1], 10).reduce((x, y) => x + y, 0), 10);
  assert.deepStrictEqual(C.allocate([0, 0], 5), [0, 0]);
});
test('갱신 일정: 샘플(2026-01-01, 1년)', () => {
  const r = C.renewalSchedule({ start: '2026-01-01', years: 1, today: TODAY });
  assert.strictEqual(r.end, '2026-12-31');
  assert.deepStrictEqual(r.notices.map(n => n.date), ['2026-11-01', '2026-12-01', '2026-12-24']);
  assert.deepStrictEqual(r.notices.map(n => n.state), ['past', 'upcoming', 'upcoming']);
  assert.strictEqual(r.daysToEnd, 44);
});
test('갱신 일정: 안내일이 오늘이면 today, 종료일 계산(윤년·말일)', () => {
  const r = C.renewalSchedule({ start: '2026-01-01', years: 1, today: '2026-12-01' });
  assert.strictEqual(r.notices[1].state, 'today');
  assert.strictEqual(C.renewalSchedule({ start: '2024-02-29', years: 1, today: TODAY }).end, '2025-02-27');
  assert.strictEqual(C.renewalSchedule({ start: '2026-03-15', years: 2, today: TODAY }).end, '2028-03-14');
});
test('갱신 일정: 잘못된 입력은 오류', () => {
  assert.ok(C.renewalSchedule({ start: '2026-13-01', years: 1, today: TODAY }).error);
  assert.ok(C.renewalSchedule({ start: '2026-01-01', years: 0, today: TODAY }).error);
  assert.ok(C.renewalSchedule({ start: '2026-01-01', years: 1, today: '' }).error);
});
test('같은 입력은 항상 같은 결과(Date.now 비의존)', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'core.js'), 'utf8');
  assert.ok(!/Date\.now|new Date\(\)/.test(src));
  assert.deepStrictEqual(chk('2026-12-01'), chk('2026-12-01'));
});
test('화면 파일: 외부 주소 없음, viewport, core.js 사용, 샘플 오늘 값', () => {
  const dir = path.join(__dirname, '..', 'app');
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.ok(html.includes('name="viewport"'));
  assert.ok(html.includes('src="core.js"'));
  assert.ok(html.includes('localStorage'));
  for (const f of ['index.html', 'core.js', 'style.css']) {
    assert.ok(!/https?:\/\//.test(fs.readFileSync(path.join(dir, f), 'utf8')), f + ' 에 http 주소');
  }
  const m = /<script>([\s\S]*?)<\/script>/.exec(html);
  assert.doesNotThrow(() => new Function(m[1]));
});
