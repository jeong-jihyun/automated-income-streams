'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');

test('금액 한글 표기', () => {
  assert.strictEqual(C.moneyToHangul(0), '영');
  assert.strictEqual(C.moneyToHangul(1), '일');
  assert.strictEqual(C.moneyToHangul(10), '일십');
  assert.strictEqual(C.moneyToHangul(3500000), '삼백오십만');
  assert.strictEqual(C.moneyToHangul(10000), '일만');
  assert.strictEqual(C.moneyToHangul(100000000), '일억');
  assert.strictEqual(C.moneyToHangul(123456789), '일억이천삼백사십오만육천칠백팔십구');
  assert.strictEqual(C.moneyToHangul(1000000000000), '일조');
  assert.strictEqual(C.moneyToHangul(-1), null);
  assert.strictEqual(C.moneyToHangul(1.5), null);
  assert.strictEqual(C.moneyToHangul(NaN), null);
});

test('금액 읽기·표시', () => {
  assert.strictEqual(C.parseMoney('1,234,000'), 1234000);
  assert.strictEqual(C.parseMoney('500원'), 500);
  assert.strictEqual(C.parseMoney('12a'), null);
  assert.strictEqual(C.parseMoney('-5'), null);
  assert.strictEqual(C.parseMoney(''), null);
  assert.strictEqual(C.formatWon(1234567), '1,234,567');
});

test('날짜 읽기', () => {
  assert.strictEqual(C.parseDate('2026-12-01'), 20261201);
  assert.strictEqual(C.parseDate('2026-02-30'), null);
  assert.strictEqual(C.parseDate('2026-13-01'), null);
  assert.strictEqual(C.parseDate('2024-02-29'), 20240229);
  assert.strictEqual(C.parseDate('2026-2-3'), null);
  assert.strictEqual(C.formatDate('2026-12-01'), '2026년 12월 1일');
});

test('분할 합계 보존', () => {
  for (const total of [0, 1, 7, 99, 1000, 3000000, 1234567, 999999999]) {
    for (const pct of [[30, 30, 40], [50, 50], [10, 20, 30, 40], [33, 33, 34]]) {
      const parts = C.splitPayment(total, pct);
      assert.strictEqual(parts.reduce((a, b) => a + b, 0), total);
      assert.ok(parts.every((p) => p >= 0 && Number.isInteger(p)));
    }
  }
  assert.strictEqual(C.splitPayment(100, [50, 40]), null);
  assert.strictEqual(C.splitPayment(-1, [100]), null);
});

test('샘플은 세 템플릿 모두 통과', () => {
  for (const t of C.TEMPLATES) {
    const r = C.build(t.id, C.sampleValues(t.id));
    assert.deepStrictEqual(r.check.missing, [], t.id);
    assert.deepStrictEqual(r.check.errors, [], t.id);
    assert.ok(r.check.ok, t.id);
    assert.ok(!/【/.test(r.text), t.id + ' 빈칸 표시가 남음');
    assert.ok(!/\{\{/.test(r.text), t.id + ' 치환 안 된 칸');
  }
});

test('샘플 본문에 값이 들어가고 한글 금액이 맞다', () => {
  const r = C.build('service', C.sampleValues('service'));
  assert.ok(r.text.includes('김하늘'));
  assert.ok(r.text.includes('일금 삼백만원정(₩3,000,000)'));
  assert.ok(r.text.includes('2026년 12월 1일'));
});

test('비어 있는 칸을 찾아 표시', () => {
  const v = C.sampleValues('service');
  v['갑'] = ''; v['총액'] = '  ';
  const r = C.build('service', v);
  assert.ok(r.check.missing.includes('갑(발주자) 이름'));
  assert.ok(r.check.missing.includes('총 대금(원)'));
  assert.ok(!r.check.ok);
  assert.ok(r.text.includes('【갑(발주자) 이름 입력 필요】'));
  assert.ok(r.text.includes('【총 대금(원) 입력 필요】'));
});

test('선택 칸이 비어 있어도 통과', () => {
  const v = C.sampleValues('service');
  v['특약'] = ''; v['총액한글입력'] = '';
  const r = C.build('service', v);
  assert.ok(r.check.ok);
  assert.ok(r.text.includes('(없음)'));
});

test('대금 합계가 안 맞으면 오류, 차액을 알려 줌', () => {
  const v = C.sampleValues('service');
  v['잔금'] = '1000000';
  const r = C.build('service', v);
  assert.ok(!r.check.ok);
  assert.ok(r.check.errors.some((e) => e.includes('200,000원') && e.includes('모자랍니다')));
  v['잔금'] = '1300000';
  const r2 = C.build('service', v);
  assert.ok(r2.check.errors.some((e) => e.includes('100,000원') && e.includes('많습니다')));
});

test('자동 나누기 결과는 항상 합계 통과', () => {
  const v = C.sampleValues('service');
  v['총액'] = '1234567'; v['총액한글입력'] = '';
  const p = C.splitPayment(1234567, [30, 30, 40]);
  v['계약금'] = String(p[0]); v['중도금'] = String(p[1]); v['잔금'] = String(p[2]);
  assert.ok(C.build('service', v).check.ok);
});

test('날짜 순서 오류', () => {
  const v = C.sampleValues('service');
  v['시작일'] = '2027-03-01'; // 종료일(2027-01-31)보다 늦음
  let r = C.build('service', v);
  assert.ok(r.check.errors.some((e) => e.includes('시작일이 종료일보다 늦습니다')));
  const v2 = C.sampleValues('service');
  v2['계약일'] = '2026-12-20'; // 시작일 12-05 보다 늦음
  r = C.build('service', v2);
  assert.ok(r.check.errors.some((e) => e.includes('계약일이 용역 시작일보다 늦습니다')));
  const v3 = C.sampleValues('service');
  v3['잔금일'] = '2026-11-01';
  r = C.build('service', v3);
  assert.ok(r.check.errors.some((e) => e.includes('잔금 지급일이 계약일보다 빠릅니다')));
  const v4 = C.sampleValues('service');
  v4['잔금일'] = '2027-01-15';
  r = C.build('service', v4);
  assert.ok(r.check.ok);
  assert.ok(r.check.warnings.length >= 1);
});

test('존재하지 않는 날짜와 잘못된 금액', () => {
  const v = C.sampleValues('lease');
  v['시작일'] = '2027-02-30';
  v['보증금'] = '2천만';
  const r = C.build('lease', v);
  assert.ok(r.check.errors.some((e) => e.includes('올바른 날짜가 아닙니다')));
  assert.ok(r.check.errors.some((e) => e.includes('숫자만')));
  assert.ok(!r.check.ok);
});

test('임대차: 기간 순서, 월세일 범위, 월세 0 경고', () => {
  const v = C.sampleValues('lease');
  v['종료일'] = '2027-01-01';
  assert.ok(C.build('lease', v).check.errors.some((e) => e.includes('시작일이 종료일과 같거나')));
  const v2 = C.sampleValues('lease');
  v2['월세일'] = '32';
  assert.ok(C.build('lease', v2).check.errors.some((e) => e.includes('1~31')));
  const v3 = C.sampleValues('lease');
  v3['월세'] = '0';
  const r3 = C.build('lease', v3);
  assert.ok(r3.check.ok);
  assert.ok(r3.check.warnings.some((w) => w.includes('월세가 0원')));
});

test('차용증: 변제일 순서와 이자율 경고', () => {
  const v = C.sampleValues('loan');
  v['변제일'] = '2026-11-01';
  assert.ok(C.build('loan', v).check.errors.some((e) => e.includes('변제일이 차용일보다 빠릅니다')));
  const v2 = C.sampleValues('loan');
  v2['이자율'] = '25';
  const r2 = C.build('loan', v2);
  assert.ok(r2.check.ok);
  assert.ok(r2.check.warnings.some((w) => w.includes('20%')));
});

test('직접 쓴 한글 금액 대조', () => {
  const v = C.sampleValues('service');
  v['총액한글입력'] = '삼백만원정';
  assert.ok(C.build('service', v).check.ok);
  v['총액한글입력'] = '일금 삼백만 원정';
  assert.ok(C.build('service', v).check.ok);
  v['총액한글입력'] = '이백만';
  const r = C.build('service', v);
  assert.ok(!r.check.ok);
  assert.ok(r.check.errors.some((e) => e.includes('다릅니다')));
  assert.ok(C.hangulMatches(10000, '만'));
  assert.ok(C.hangulMatches(10000, '일만'));
  assert.ok(!C.hangulMatches(10000, '십만'));
});

test('0원 불가 칸 / 같은 이름 경고', () => {
  const v = C.sampleValues('loan');
  v['금액'] = '0';
  assert.ok(C.build('loan', v).check.errors.some((e) => e.includes('0보다 커야')));
  const v2 = C.sampleValues('loan');
  v2['채무자'] = v2['채권자'];
  assert.ok(C.build('loan', v2).check.warnings.some((w) => w.includes('이름이 같습니다')));
});

test('알 수 없는 템플릿은 null, 법률 자문 아님 문구 포함', () => {
  assert.strictEqual(C.build('nope', {}), null);
  assert.ok(C.DISCLAIMER.includes('법률 자문이 아닙니다'));
  assert.ok(C.build('loan', C.sampleValues('loan')).disclaimer.includes('법률 자문'));
});

test('앱 파일: 외부 주소 없음, core.js 연결, viewport', () => {
  const dir = path.join(__dirname, '..', 'app');
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  const css = fs.readFileSync(path.join(dir, 'style.css'), 'utf8');
  const js = fs.readFileSync(path.join(dir, 'core.js'), 'utf8');
  for (const s of [html, css, js]) assert.ok(!/https?:\/\//.test(s));
  assert.ok(html.includes('<script src="core.js"></script>'));
  assert.ok(html.includes('name="viewport"'));
  assert.ok(!/fetch\(|XMLHttpRequest|WebSocket/.test(html + js));
});
