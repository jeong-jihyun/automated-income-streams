'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');
const J = (o) => C.judge(Object.assign({ type: 'company', employees: 10, saas: false }, o));

test('개인은 무료', () => assert.strictEqual(J({ type: 'individual' }).verdict, 'free'));
test('비영리는 무료', () => assert.strictEqual(J({ type: 'nonprofit', employees: 500 }).verdict, 'free'));
test('회사는 유료와 구간 사유', () => {
  const r = J({ employees: 30 });
  assert.strictEqual(r.verdict, 'paid');
  assert.strictEqual(r.tier.max, 49);
  assert.ok(r.reasons.join('').includes('49명'));
});
test('구간 경계 9/10, 49/50, 999/1000', () => {
  assert.strictEqual(J({ employees: 9 }).tier.max, 9);
  assert.strictEqual(J({ employees: 10 }).tier.max, 49);
  assert.strictEqual(J({ employees: 49 }).tier.max, 49);
  assert.strictEqual(J({ employees: 50 }).tier.max, 249);
  assert.strictEqual(J({ employees: 999 }).verdict, 'paid');
  assert.strictEqual(J({ employees: 1000 }).verdict, 'inquiry');
});
test('SaaS 내장 재배포는 누구든 문의 필요', () => {
  ['individual', 'nonprofit', 'company'].forEach(t => assert.strictEqual(J({ type: t, saas: true }).verdict, 'inquiry'));
});
test('잘못된 입력은 문의 필요(오류)', () => {
  assert.ok(J({ employees: -1 }).error);
  assert.ok(J({ employees: 1.5 }).error);
  assert.ok(J({ employees: 'abc' }).error);
  assert.ok(J({ type: '' }).error);
});
test('구간표 읽기와 오류', () => {
  assert.strictEqual(C.parseTiers(C.DEFAULT_TIERS_TEXT).tiers.length, 4);
  assert.ok(C.parseTiers('10,100\n5,200').errors.length > 0);
  assert.ok(C.parseTiers('abc').errors.length > 0);
  assert.ok(C.parseTiers('').errors.length > 0);
  assert.ok(J({ tiersText: 'x' }).error);
});
test('견적: 1년은 할인 없음', () => {
  const q = C.quote({ employees: 30, devs: 5, years: 1, disc2: 5, disc3: 10 });
  assert.strictEqual(q.gross, 1500000);
  assert.strictEqual(q.discount, 0);
  assert.strictEqual(q.vat, 150000);
  assert.strictEqual(q.total, 1650000);
});
test('견적: 2년·3년 할인 경계', () => {
  assert.strictEqual(C.quote({ employees: 30, devs: 5, years: 2, disc2: 5, disc3: 10 }).discountPct, 5);
  assert.strictEqual(C.quote({ employees: 30, devs: 5, years: 3, disc2: 5, disc3: 10 }).discountPct, 10);
  assert.strictEqual(C.quote({ employees: 30, devs: 5, years: 5, disc2: 5, disc3: 10 }).discountPct, 10);
});
test('견적: 합계 보존(여러 조합)', () => {
  for (let devs = 1; devs <= 13; devs++) for (let years = 1; years <= 7; years++) for (const emp of [3, 30, 100, 700]) {
    const q = C.quote({ employees: emp, devs, years, disc2: 3.3, disc3: 7.7 });
    const s = q.items.reduce((a, i) => a + i.supply, 0), v = q.items.reduce((a, i) => a + i.vat, 0);
    assert.strictEqual(s, q.supply);
    assert.strictEqual(v, q.vat);
    assert.strictEqual(q.supply + q.vat, q.total);
    assert.strictEqual(q.items.reduce((a, i) => a + i.total, 0), q.total);
    assert.strictEqual(q.gross - q.discount, q.supply);
  }
});
test('견적: 입력 오류', () => {
  assert.ok(C.quote({ employees: 30, devs: 0, years: 1 }).error);
  assert.ok(C.quote({ employees: 30, devs: 2, years: 0 }).error);
  assert.ok(C.quote({ employees: 30, devs: 2, years: 11 }).error);
  assert.ok(C.quote({ employees: 30, devs: 2, years: 1, disc2: 101 }).error);
  assert.ok(C.quote({ employees: 5000, devs: 2, years: 1 }).error);
  assert.ok(C.quote({ employees: 30, devs: 2.5, years: 1 }).error);
});
test('견적: 구간표를 바꾸면 반영', () => {
  const q = C.quote({ employees: 5, devs: 2, years: 1, tiersText: '10,1000' });
  assert.strictEqual(q.supply, 2000);
  assert.strictEqual(q.vat, 200);
});
test('allocate 합 보존', () => {
  assert.deepStrictEqual(C.allocate([1, 1, 1], 100).reduce((a, b) => a + b, 0), 100);
  assert.deepStrictEqual(C.allocate([0, 0], 5), [0, 0]);
});
test('CLA: 외부 기여 + 서명 없음은 불가 경고', () => {
  const r = C.claCheck({ external: true, claSigned: false, employer: true, copyleftDep: false });
  assert.strictEqual(r.status, 'blocked');
  assert.ok(r.warnings[0].includes('이중 라이선스가 불가능'));
});
test('CLA: 외부 기여 없음/서명 완료는 가능', () => {
  assert.strictEqual(C.claCheck({ external: false }).status, 'ok');
  assert.strictEqual(C.claCheck({ external: true, claSigned: true, employer: true }).status, 'ok');
});
test('CLA: 회사 허락 없음은 주의, 카피레프트는 불가', () => {
  assert.strictEqual(C.claCheck({ external: true, claSigned: true, employer: false }).status, 'warn');
  assert.strictEqual(C.claCheck({ external: false, copyleftDep: true }).status, 'blocked');
});
test('won 형식', () => { assert.strictEqual(C.won(1650000), '1,650,000원'); assert.strictEqual(C.won(0), '0원'); });
test('화면 파일: http 없음, viewport, 스크립트 문법, 필수 id', () => {
  const dir = path.join(__dirname, '..', 'app');
  ['index.html', 'core.js', 'style.css'].forEach(f => assert.ok(!/https?:\/\//.test(fs.readFileSync(path.join(dir, f), 'utf8')), f));
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.ok(html.includes('name="viewport"'));
  const m = html.match(/<script>([\s\S]*?)<\/script>/);
  new Function(m[1]);
  ['runJudge', 'runQuote', 'runCla', 'resetAll'].forEach(id => assert.ok(html.includes('id="' + id + '"')));
  assert.ok(html.includes('법률 자문이 아닙니다'));
});
