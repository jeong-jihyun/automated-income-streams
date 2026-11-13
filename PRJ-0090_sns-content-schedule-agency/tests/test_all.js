const test = require('node:test');
const assert = require('node:assert');
const C = require('../app/core.js');

const plan = (s) => C.parsePlan(s).items;

test('parsePlan: 정상 줄과 오류 줄 구분', () => {
  const r = C.parsePlan('2026-11-05, 인스타, 제목, 쉼표 포함\n2026-02-30, 블로그, x\nabc, 인스타, y\n2026-11-06, , z\n# 주석\n\n2026.11.7\t유튜브\t탭');
  assert.strictEqual(r.items.length, 2);
  assert.strictEqual(r.items[0].title, '제목, 쉼표 포함');
  assert.strictEqual(r.items[1].date, '2026-11-07');
  assert.strictEqual(r.errors.length, 3);
});

test('isValidDate: 윤년', () => {
  assert.ok(C.isValidDate(2024, 2, 29));
  assert.ok(!C.isValidDate(2026, 2, 29));
});

test('buildCalendar: 2026-11은 일요일 시작, 월요일 기준 칸', () => {
  const w = C.buildCalendar(2026, 11, []);
  assert.strictEqual(C.weekdayIdx(2026, 11, 1), 6);
  assert.strictEqual(w[0][6].day, 1);
  assert.strictEqual(w[0][0], null);
  assert.strictEqual(w.length, 6);
  assert.strictEqual(w[5][0].day, 30);
});

test('analyze: 같은 날 같은 채널 중복 (대소문자 무시, 다른 채널은 중복 아님)', () => {
  const a = C.analyze(plan('2026-11-05, 인스타, a\n2026-11-05, 인스타, b\n2026-11-05, 블로그, c\n2026-11-06, IG, d\n2026-11-06, ig, e'), { year: 2026, month: 11 });
  assert.strictEqual(a.duplicates.length, 2);
  assert.strictEqual(a.duplicates[0].count, 2);
});

test('analyze: 빈 날, 주말 제외 옵션', () => {
  const items = plan('2026-11-02, a, x');
  const all = C.analyze(items, { year: 2026, month: 11 });
  assert.strictEqual(all.emptyDays.length, 29);
  const wk = C.analyze(items, { year: 2026, month: 11, skipWeekendEmpty: true });
  // 11월 주말: 1,7,8,14,15,21,22,28,29 = 9일 / 평일 21일 중 2일 제외
  assert.strictEqual(wk.emptyDays.length, 20);
  assert.ok(!wk.emptyDays.includes(7));
});

test('analyze: 주별 게시 수 합 = 전체, 부족한 주 표시', () => {
  const a = C.analyze(plan('2026-11-02, a, x\n2026-11-03, a, x\n2026-11-04, a, x\n2026-11-10, a, x'), { year: 2026, month: 11, minPerWeek: 3 });
  assert.strictEqual(a.weekCounts.reduce((s, w) => s + w.count, 0), 4);
  assert.strictEqual(a.weekCounts[1].count, 3);
  assert.ok(!a.weekCounts[1].low);
  assert.ok(a.weekCounts[2].low);
});

test('analyze: 요일 쏠림', () => {
  const s = plan('2026-11-02, a, x\n2026-11-09, a, x\n2026-11-16, a, x\n2026-11-23, a, x\n2026-11-03, a, x');
  const a = C.analyze(s, { year: 2026, month: 11 });
  assert.strictEqual(a.skew.topWeekday, '월');
  assert.strictEqual(a.skew.topShare, 80);
  assert.ok(a.skew.skewed);
  const few = C.analyze(plan('2026-11-02, a, x'), { year: 2026, month: 11 });
  assert.ok(!few.skew.skewed); // 5건 미만은 판정 안 함
});

test('analyze: 선택한 달 밖의 일정은 계산에서 제외', () => {
  const a = C.analyze(plan('2026-12-01, a, x\n2026-11-03, a, y'), { year: 2026, month: 11 });
  assert.strictEqual(a.total, 1);
  assert.strictEqual(a.outside, 1);
});

test('analyze: 빈 입력도 오류 없이', () => {
  const a = C.analyze([], { year: 2026, month: 11 });
  assert.strictEqual(a.total, 0);
  assert.strictEqual(a.skew.topWeekday, null);
});

test('allocate: 합 보존 (여러 경우)', () => {
  for (const [t, w] of [[100, [1, 1, 1]], [7, [3, 3, 3]], [1, [5, 5]], [0, [1, 2]], [99999, [7, 11, 13, 17]], [10, [0, 0, 0]]]) {
    const r = C.allocate(t, w);
    assert.strictEqual(r.reduce((a, b) => a + b, 0), t);
    assert.ok(r.every((x) => Number.isInteger(x) && x >= 0));
  }
  assert.deepStrictEqual(C.allocate(100, [1, 1, 1]), [34, 33, 33]);
});

test('quote: 단가 x 게시 수, 부가세 10%, 합계', () => {
  const q = C.quote({ 인스타: 5, 블로그: 3, 유튜브: 2 }, 30000, 10);
  assert.strictEqual(q.posts, 10);
  assert.strictEqual(q.supply, 300000);
  assert.strictEqual(q.vat, 30000);
  assert.strictEqual(q.total, 330000);
});

test('quote: 채널별 합계가 전체와 정확히 일치 (나머지 처리)', () => {
  for (const unit of [33333, 1, 12345, 777, 0]) {
    const ch = { a: 3, b: 3, c: 3, d: 1 };
    const q = C.quote(ch, unit, 10);
    assert.strictEqual(q.rows.reduce((s, r) => s + r.supply, 0), q.supply);
    assert.strictEqual(q.rows.reduce((s, r) => s + r.vat, 0), q.vat);
    assert.strictEqual(q.rows.reduce((s, r) => s + r.total, 0), q.total);
    assert.strictEqual(q.total, q.supply + q.vat);
  }
});

test('quote: 게시 0건, 잘못된 단가', () => {
  const q = C.quote({}, 'abc', 10);
  assert.strictEqual(q.total, 0);
  assert.strictEqual(C.quote({ a: 1 }, -5, 10).total, 0);
});

test('won: 천 단위 쉼표', () => {
  assert.strictEqual(C.won(1234567), '1,234,567원');
  assert.strictEqual(C.won(0), '0원');
});

test('analyze: 일부 날짜만 이 달인 주는 부족 판정에서 제외', () => {
  const a = C.analyze([], { year: 2026, month: 11, minPerWeek: 3 });
  assert.ok(a.weekCounts[0].partial && !a.weekCounts[0].low);
  assert.ok(a.weekCounts[1].low);
  assert.strictEqual(a.weekCounts.filter((w) => w.low).length, 4); // 2~5주차
});
