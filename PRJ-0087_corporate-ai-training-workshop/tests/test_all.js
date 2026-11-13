const test = require('node:test');
const assert = require('node:assert');
const C = require('../app/core.js');

test('splitCost: 합이 총액과 같다 (나머지 있음)', () => {
  const a = C.splitCost(100, 3);
  assert.deepStrictEqual(a, [34, 33, 33]);
  assert.strictEqual(a.reduce((x, y) => x + y, 0), 100);
});
test('splitCost: 여러 조합에서 합 보존', () => {
  for (const total of [0, 1, 7, 999, 1115000, 1234567]) for (const n of [1, 2, 3, 7, 13, 20, 101]) {
    const a = C.splitCost(total, n);
    assert.strictEqual(a.length, n);
    assert.strictEqual(a.reduce((x, y) => x + y, 0), total);
    assert.ok(Math.max(...a) - Math.min(...a) <= 1);
  }
});
test('splitCost: n<1 오류', () => assert.throws(() => C.splitCost(100, 0)));
test('샘플 계산: 총비용·매출·손익', () => {
  const r = C.calcWorkshop(C.SAMPLE);
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.totalCost, 800000 + 300000 + 15000 * 20); // 1,400,000
  assert.strictEqual(r.revenue, 1800000);
  assert.strictEqual(r.profit, 400000);
  assert.strictEqual(r.shareSum, r.totalCost);
});
test('손익분기 인원: 1,100,000 / 75,000 = 14.67 -> 15', () => {
  assert.strictEqual(C.breakEven(C.SAMPLE), 15);
  assert.ok(C.scenario(C.SAMPLE, 15).profit >= 0);
  assert.ok(C.scenario(C.SAMPLE, 14).profit < 0);
});
test('손익분기: 참가비<=자료비면 null', () => {
  assert.strictEqual(C.breakEven({ ...C.SAMPLE, pricePerPerson: 15000 }), null);
  const r = C.calcWorkshop({ ...C.SAMPLE, pricePerPerson: 10000 });
  assert.strictEqual(r.breakEven, null);
});
test('손익분기: 고정비 0이면 1명', () => {
  assert.strictEqual(C.breakEven({ ...C.SAMPLE, instructorFee: 0, venueFee: 0 }), 1);
});
test('적자 문구', () => {
  const r = C.calcWorkshop({ ...C.SAMPLE, headcount: 10 });
  assert.ok(r.profit < 0);
  assert.match(r.verdict, /모자라요/);
});
test('입력 검증: 빈값·음수·0명·글자', () => {
  assert.ok(C.calcWorkshop({ ...C.SAMPLE, instructorFee: '' }).errors.length > 0);
  assert.ok(C.calcWorkshop({ ...C.SAMPLE, venueFee: -1 }).errors.length > 0);
  assert.ok(C.calcWorkshop({ ...C.SAMPLE, headcount: 0 }).errors.length > 0);
  assert.ok(C.calcWorkshop({ ...C.SAMPLE, pricePerPerson: 'abc' }).errors.length > 0);
});
test('쉼표·단위가 붙은 입력도 읽는다', () => {
  assert.strictEqual(C.toInt('1,200,000원'), 1200000);
  const r = C.calcWorkshop({ ...C.SAMPLE, instructorFee: '800,000' });
  assert.strictEqual(r.ok, true);
});
test('나머지 있는 총비용에서도 인원별 분담 합 보존', () => {
  const r = C.calcWorkshop({ instructorFee: 1000001, venueFee: 0, materialPerPerson: 0, headcount: 7, pricePerPerson: 200000 });
  assert.strictEqual(r.shareSum, 1000001);
  assert.strictEqual(r.perPersonCost.length, 7);
});
test('표: 비용 = 고정비 + 자료비*인원, 손익 = 매출-비용', () => {
  const r = C.calcWorkshop(C.SAMPLE);
  for (const t of r.table) {
    assert.strictEqual(t.cost, 1100000 + 15000 * t.n);
    assert.strictEqual(t.profit, t.revenue - t.cost);
  }
  assert.ok(r.table.some(t => t.n === 20));
});
test('체크리스트: 샘플 점수', () => {
  const r = C.scoreChecklist(C.CHECK_SAMPLE);
  assert.strictEqual(r.score, 9);
  assert.strictEqual(r.max, 14);
  assert.strictEqual(r.percent, 64);
  assert.strictEqual(r.level, '활용 중');
  assert.strictEqual(r.notUsed.length, 1);
});
test('체크리스트: 빈 답은 시작 단계, 전부 자주는 활용 잘함', () => {
  assert.strictEqual(C.scoreChecklist({}).level, '시작 단계');
  const all = {}; C.CHECK_ITEMS.forEach(i => all[i.id] = 2);
  const r = C.scoreChecklist(all);
  assert.strictEqual(r.percent, 100); assert.strictEqual(r.level, '활용 잘함');
});
test('체크리스트: 이상한 값은 0 처리', () => {
  assert.strictEqual(C.scoreChecklist({ mail: 9, minutes: 'x' }).score, 0);
});
test('앱 파일에 외부 주소 없음', () => {
  const fs = require('fs'), p = require('path');
  for (const f of ['index.html', 'core.js', 'style.css']) {
    const s = fs.readFileSync(p.join(__dirname, '../app', f), 'utf8');
    assert.ok(!/https?:\/\//.test(s), f);
    assert.ok(!/fetch\(|XMLHttpRequest/.test(s), f);
  }
});
