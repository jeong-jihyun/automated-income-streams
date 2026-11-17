'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');

const day = (inS, outS, s) => C.calcDay({ inMin: inS === null ? null : C.parseTime(inS), outMin: outS === null ? null : C.parseTime(outS) }, s || {});

test('시각·날짜 읽기', () => {
  assert.strictEqual(C.parseTime('09:30'), 570);
  assert.strictEqual(C.parseTime('24:00'), null);
  assert.strictEqual(C.parseTime('9:60'), null);
  assert.strictEqual(C.parseDate('2026-2-30'), null);
  assert.strictEqual(C.parseDate('2026/11/3'), '2026-11-03');
});
test('기록 읽기: 정상·누락·오류 줄', () => {
  const r = C.parseRecords('# 메모\n홍길동 2026-11-02 09:00 18:00\n김 2026-11-02 - 18:00\n나쁨 2026-11-02 09:00\n다른 2026-13-02 09:00 18:00\n같음 2026-11-02 09:00 09:00\n시각 2026-11-02 9:99 18:00');
  assert.strictEqual(r.records.length, 2);
  assert.strictEqual(r.records[1].inMin, null);
  assert.strictEqual(r.errors.length, 4);
  assert.ok(r.errors[0].startsWith('4번째 줄'));
});
test('보통 근무: 9~18시, 휴게 60분, 연장 없음', () => {
  const d = day('09:00', '18:00');
  assert.deepStrictEqual([d.grossMin, d.breakMin, d.workMin, d.otMin, d.nightMin, d.lateMin, d.earlyMin], [540, 60, 480, 0, 0, 0, 0]);
});
test('휴게 단계: 4시간 미만 0, 4시간 이상 30분, 8시간 이상 60분', () => {
  assert.strictEqual(day('09:00', '12:59').breakMin, 0);
  assert.strictEqual(day('09:00', '13:00').breakMin, 30);
  assert.strictEqual(day('09:00', '16:59').breakMin, 30);
  assert.strictEqual(day('09:00', '17:00').breakMin, 60);
});
test('연장: 소정 8시간 초과분, 기준 바꾸면 달라짐', () => {
  assert.strictEqual(day('09:00', '20:00').otMin, 120);
  assert.strictEqual(day('09:00', '20:00', { stdHours: 7 }).otMin, 180);
});
test('자정 넘김: 22시~06시 야간, 휴게 뺀 근무시간 이내로 제한', () => {
  const d = day('22:00', '06:00');
  assert.strictEqual(d.grossMin, 480);
  assert.strictEqual(d.workMin, 420);
  assert.strictEqual(d.nightMin, 420);
  assert.strictEqual(d.lateMin, 0);
  assert.strictEqual(d.earlyMin, 0);
});
test('야간 겹침: 20~24시는 2시간, 0~7시는 6시간, 기준 바꾸면 달라짐', () => {
  assert.strictEqual(C.nightOverlap(20 * 60, 24 * 60, 22, 6), 120);
  assert.strictEqual(C.nightOverlap(0, 7 * 60, 22, 6), 360);
  assert.strictEqual(C.nightOverlap(0, 7 * 60, 23, 5), 300);
  assert.strictEqual(C.nightOverlap(1320, 1800, 22, 22), 0);
});
test('지각·조퇴와 봐주는 분', () => {
  assert.strictEqual(day('09:12', '18:00').lateMin, 12);
  assert.strictEqual(day('09:12', '18:00', { graceMin: 15 }).lateMin, 0);
  assert.strictEqual(day('09:00', '17:30').earlyMin, 30);
  assert.strictEqual(day('09:00', '17:50', { graceMin: 10 }).earlyMin, 0);
  assert.strictEqual(day('08:30', '18:30').lateMin, 0);
});
test('누락: 출근만/퇴근만/둘 다 없음은 시간 0', () => {
  assert.strictEqual(day('09:00', null).missing, 'out');
  assert.strictEqual(day(null, '18:00').missing, 'in');
  assert.strictEqual(day(null, null).missing, 'both');
  assert.strictEqual(day('09:00', null).workMin, 0);
});
test('집계: 누락 경고와 월 합계', () => {
  const r = C.summarize(C.SAMPLE_TEXT, {}, C.SAMPLE_WAGES);
  assert.strictEqual(r.errors.length, 0);
  assert.strictEqual(r.employees.length, 3);
  assert.strictEqual(r.warnings.filter(w => w.type === 'missing-out').length, 1);
  assert.strictEqual(r.warnings.filter(w => w.type === 'missing-in').length, 1);
  const h = r.employees[0];
  assert.strictEqual(h.name, '홍길동');
  assert.strictEqual(h.workMin, 1068);
  assert.strictEqual(h.otMin, 120);
  assert.strictEqual(h.lateCount, 1);
  assert.strictEqual(h.missingCount, 1);
  assert.strictEqual(h.pay, 197400);
  assert.strictEqual(r.totals.pay, 605040);
});
test('급여 합계 보존: 직원 합 = 총액 (여러 시급·가산)', () => {
  for (const wage of [9999, 10320, 12345]) for (const prem of [0, 0.5, 0.33]) {
    const txt = '가 2026-11-01 09:07 20:41\n나 2026-11-01 21:13 06:29\n다 2026-11-02 08:55 17:01\n나 2026-11-02 09:00 -\n라 2026-11-03 10:00 15:59';
    const r = C.summarize(txt, { defaultWage: wage, otPremium: prem, nightPremium: prem }, '다=' + (wage + 77));
    assert.strictEqual(r.employees.reduce((a, e) => a + e.pay, 0), r.totals.pay);
    const exact = r.employees.reduce((a, e) => a + e.payRaw, 0);
    assert.strictEqual(r.totals.pay, Math.round(exact));
    r.employees.forEach(e => { assert.ok(Number.isInteger(e.pay) && e.pay >= 0); assert.ok(Math.abs(e.pay - e.payRaw) < 1); });
  }
});
test('allocate는 합을 정확히 보존', () => {
  const a = C.allocate([1, 1, 1], 10);
  assert.strictEqual(a.reduce((x, y) => x + y, 0), 10);
  assert.deepStrictEqual(C.allocate([0, 0], 5), [0, 0]);
});
test('집계 월 필터·잘못된 월·같은 날 중복·너무 긴 근무 경고', () => {
  const txt = '가 2026-10-31 09:00 18:00\n가 2026-11-01 09:00 18:00\n가 2026-11-01 19:00 20:00\n나 2026-11-02 06:00 23:30';
  const all = C.summarize(txt, {});
  assert.strictEqual(all.days.length, 4);
  assert.ok(all.warnings.some(w => w.type === 'dup'));
  const nov = C.summarize(txt, { month: '2026-11' });
  assert.strictEqual(nov.days.length, 3);
  assert.ok(C.summarize(txt, { month: '11월' }).errors.length > 0);
  const long = C.summarize('다 2026-11-02 06:00 23:30', {});
  assert.ok(long.warnings.some(w => w.type === 'long'));
});
test('빈 입력·이상한 설정은 죽지 않음', () => {
  const r = C.summarize('', { stdHours: 'abc', defaultWage: -5, nightStart: 99 });
  assert.strictEqual(r.employees.length, 0);
  assert.strictEqual(r.totals.pay, 0);
  assert.strictEqual(C.normalize({ stdHours: 'abc' }).stdHours, 8);
});
test('시급 목록 읽기', () => {
  const w = C.parseWages('홍길동=10,500\n김 12000원\n# 메모\n이상한줄');
  assert.strictEqual(w.map['홍길동'], 10500);
  assert.strictEqual(w.map['김'], 12000);
  assert.strictEqual(w.errors.length, 1);
});
test('화면 파일: 외부 주소 없음, viewport, core.js 사용, 예시값 표시, 저장은 try/catch', () => {
  const dir = path.join(__dirname, '..', 'app');
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.ok(html.includes('name="viewport"'));
  assert.ok(html.includes('src="core.js"'));
  assert.ok(html.includes('예시값') && html.includes('자문이 아닙니다'));
  assert.ok(/try \{[^]*localStorage/.test(html));
  const inline = /<script>([^]*?)<\/script>/.exec(html)[1];
  new Function(inline);
  for (const f of ['index.html', 'core.js', 'style.css']) {
    assert.ok(!/https?:\/\//.test(fs.readFileSync(path.join(dir, f), 'utf8')), f + ' 에 http 주소');
  }
});
