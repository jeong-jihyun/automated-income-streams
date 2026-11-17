'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');

const P = () => Object.assign({}, C.SAMPLE_PROFILE);
const G = (o) => Object.assign({ id: 'T', name: 't', agency: 'a', deadline: '2026-12-31', amount: 100, focus: 'f' }, o);

test('날짜 읽기와 잘못된 날짜', () => {
  assert.strictEqual(C.parseDate('2026-02-30'), null);
  assert.strictEqual(C.parseDate('2026-1-5'), null);
  assert.strictEqual(C.parseDate(''), null);
  assert.strictEqual(C.parseDate('2024-02-29') !== null, true);
  assert.strictEqual(C.parseDate('2026-02-29'), null);
});
test('남은 날 계산: 월 경계·오늘·지남', () => {
  assert.strictEqual(C.daysLeft('2026-12-01', '2026-11-30'), 1);
  assert.strictEqual(C.daysLeft('2026-11-17', '2026-11-17'), 0);
  assert.strictEqual(C.daysLeft('2026-11-16', '2026-11-17'), -1);
  assert.strictEqual(C.daysLeft('2027-01-01', '2026-12-31'), 1);
  assert.strictEqual(C.daysLeft('x', '2026-12-31'), null);
});
test('D 표시', () => {
  assert.strictEqual(C.dLabel(3), 'D-3');
  assert.strictEqual(C.dLabel(0), '오늘 마감');
  assert.strictEqual(C.dLabel(-1), '마감 지남');
  assert.strictEqual(C.dLabel(null), '날짜 확인 필요');
});
test('입력 검증', () => {
  assert.deepStrictEqual(C.validateProfile(P()), []);
  assert.ok(C.validateProfile(Object.assign(P(), { industry: '' })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { bizYears: -1 })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { bizYears: '' })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { employees: 1.5 })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { repAge: 14 })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { repAge: 101 })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { today: '2026-13-01' })).length);
  assert.ok(C.validateProfile(Object.assign(P(), { region: '화성' })).length);
  assert.deepStrictEqual(C.validateProfile(Object.assign(P(), { bizYears: 0, employees: 0, repAge: 15 })), []);
  assert.ok(C.validateProfile(null).length);
});
test('업종 일치·불일치', () => {
  assert.strictEqual(C.evaluate(P(), G({ industries: ['음식점업'] })).status, 'eligible');
  const r = C.evaluate(P(), G({ industries: ['제조업'] }));
  assert.strictEqual(r.status, 'ineligible');
  assert.ok(r.reasons[0].includes('업종 불일치'));
});
test('빈 업종·지역 목록은 제한 없음', () => {
  assert.strictEqual(C.evaluate(P(), G({ industries: [], regions: [] })).status, 'eligible');
  assert.strictEqual(C.evaluate(P(), G({})).status, 'eligible');
});
test('지역 불일치', () => {
  const r = C.evaluate(P(), G({ regions: ['부산'] }));
  assert.strictEqual(r.status, 'ineligible');
  assert.ok(r.reasons[0].includes('지역 불일치'));
});
test('업력 경계값(포함)', () => {
  const p = P(); p.bizYears = 3;
  assert.strictEqual(C.evaluate(p, G({ maxBizYears: 3 })).status, 'eligible');
  p.bizYears = 3.5;
  assert.strictEqual(C.evaluate(p, G({ maxBizYears: 3 })).status, 'ineligible');
  p.bizYears = 1;
  assert.strictEqual(C.evaluate(p, G({ minBizYears: 1 })).status, 'eligible');
  p.bizYears = 0.5;
  const r = C.evaluate(p, G({ minBizYears: 1 }));
  assert.strictEqual(r.status, 'ineligible');
  assert.ok(r.reasons[0].includes('업력 부족'));
});
test('직원 수 경계값(포함)', () => {
  const p = P(); p.employees = 9;
  assert.strictEqual(C.evaluate(p, G({ maxEmployees: 9 })).status, 'eligible');
  p.employees = 10;
  assert.ok(C.evaluate(p, G({ maxEmployees: 9 })).reasons[0].includes('직원 수 초과'));
  p.employees = 2;
  assert.strictEqual(C.evaluate(p, G({ minEmployees: 2 })).status, 'eligible');
  p.employees = 1;
  assert.ok(C.evaluate(p, G({ minEmployees: 2 })).reasons[0].includes('직원 수 부족'));
  p.employees = 0;
  assert.strictEqual(C.evaluate(p, G({ maxEmployees: 0 })).status, 'eligible');
});
test('대표 나이 경계값(포함)', () => {
  const p = P(); p.repAge = 39;
  assert.strictEqual(C.evaluate(p, G({ minRepAge: 19, maxRepAge: 39 })).status, 'eligible');
  p.repAge = 40;
  assert.ok(C.evaluate(p, G({ maxRepAge: 39 })).reasons[0].includes('대표 나이 초과'));
  p.repAge = 19;
  assert.strictEqual(C.evaluate(p, G({ minRepAge: 19 })).status, 'eligible');
  p.repAge = 18;
  assert.ok(C.evaluate(p, G({ minRepAge: 19 })).reasons[0].includes('대표 나이 미달'));
});
test('불일치 사유가 여러 개면 모두 나온다', () => {
  const r = C.evaluate(P(), G({ industries: ['제조업'], regions: ['부산'], maxEmployees: 1 }));
  assert.strictEqual(r.reasons.length, 3);
});
test('마감: 오늘이면 아직 신청 가능, 어제면 마감', () => {
  assert.strictEqual(C.evaluate(P(), G({ deadline: '2026-11-17' })).status, 'eligible');
  assert.strictEqual(C.evaluate(P(), G({ deadline: '2026-11-16' })).status, 'closed');
  assert.strictEqual(C.evaluate(P(), G({ deadline: '잘못' })).status, 'closed');
});
test('임박 표시는 7일 이내', () => {
  assert.strictEqual(C.evaluate(P(), G({ deadline: '2026-11-24' })).urgent, true);
  assert.strictEqual(C.evaluate(P(), G({ deadline: '2026-11-25' })).urgent, false);
  assert.strictEqual(C.evaluate(P(), G({ deadline: '2026-11-16' })).urgent, false);
});
test('정렬: 일치 → 불일치 → 마감, 마감 임박순, 같은 날은 번호순', () => {
  const gs = [
    G({ id: 'A', deadline: '2026-12-20' }),
    G({ id: 'B', deadline: '2026-11-18' }),
    G({ id: 'C', deadline: '2026-11-18' }),
    G({ id: 'D', deadline: '2026-11-19', industries: ['제조업'] }),
    G({ id: 'E', deadline: '2026-11-01' }),
    G({ id: 'F', deadline: '2026-11-10' })
  ];
  const ids = C.rank(P(), gs).results.map(r => r.id);
  assert.deepStrictEqual(ids, ['B', 'C', 'A', 'D', 'F', 'E']);
});
test('rank는 잘못된 입력에 오류만 돌려준다', () => {
  const r = C.rank(Object.assign(P(), { repAge: '' }), C.SAMPLE_GRANTS);
  assert.ok(r.errors.length);
  assert.strictEqual(r.results.length, 0);
});
test('샘플 데이터 결과(샘플 조건)', () => {
  const r = C.rank(C.SAMPLE_PROFILE, C.SAMPLE_GRANTS);
  const by = {}; r.results.forEach(x => { by[x.id] = x.status; });
  assert.strictEqual(by.G01, 'eligible');
  assert.strictEqual(by.G02, 'eligible');
  assert.strictEqual(by.G03, 'ineligible');
  assert.strictEqual(by.G04, 'eligible');
  assert.strictEqual(by.G05, 'ineligible');
  assert.strictEqual(by.G06, 'ineligible');
  assert.strictEqual(by.G07, 'closed');
  assert.strictEqual(r.results[0].id, 'G01');
  const s = C.summarize(r.results);
  assert.strictEqual(s.eligible, 3);
  assert.strictEqual(s.closed, 1);
  assert.strictEqual(s.urgent, 1);
  assert.strictEqual(s.eligible + s.ineligible + s.closed, C.SAMPLE_GRANTS.length);
});
test('샘플 공고는 이름에 (예시)가 붙고 날짜가 올바르다', () => {
  C.SAMPLE_GRANTS.forEach(g => {
    assert.ok(g.name.startsWith('(예시)'));
    assert.notStrictEqual(C.parseDate(g.deadline), null);
  });
  assert.strictEqual(new Set(C.SAMPLE_GRANTS.map(g => g.id)).size, C.SAMPLE_GRANTS.length);
});
test('금액 표시', () => {
  assert.strictEqual(C.won(3000), '3,000만 원');
  assert.strictEqual(C.won(500), '500만 원');
});
test('초안: 문단 7개, 공고명·마감일·금액 포함, 빈칸 남김', () => {
  const g = C.SAMPLE_GRANTS[0];
  const d = C.draftApplication(C.SAMPLE_PROFILE, g);
  assert.deepStrictEqual(d.errors, []);
  assert.strictEqual(d.paragraphs.length, 7);
  assert.ok(d.text.includes(g.name));
  assert.ok(d.text.includes('2026-11-20'));
  assert.ok(d.text.includes('500만 원'));
  assert.ok(d.text.includes('[상호명]'));
  assert.strictEqual(d.warning, '');
});
test('초안: 자격 불일치·마감이면 경고', () => {
  const bad = C.draftApplication(C.SAMPLE_PROFILE, C.SAMPLE_GRANTS[2]);
  assert.ok(bad.warning.includes('자격 불일치'));
  const closed = C.draftApplication(C.SAMPLE_PROFILE, C.SAMPLE_GRANTS[6]);
  assert.ok(closed.warning.includes('마감'));
});
test('초안: 잘못된 입력·공고 없음은 오류', () => {
  assert.ok(C.draftApplication(Object.assign(P(), { industry: '' }), C.SAMPLE_GRANTS[0]).errors.length);
  assert.ok(C.draftApplication(P(), null).errors.length);
});
test('화면 파일: 가상 예시 표시, viewport, http 없음, 외부 연결 없음', () => {
  const dir = path.join(__dirname, '..', 'app');
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.ok(html.includes('가상 예시'));
  assert.ok(html.includes('실제 공고가 아닙니다'));
  assert.ok(html.includes('name="viewport"'));
  assert.ok(html.includes('core.js'));
  ['index.html', 'core.js', 'style.css'].forEach(f => {
    const t = fs.readFileSync(path.join(dir, f), 'utf8');
    assert.ok(!/https?:\/\//.test(t), f + ' http 주소');
    assert.ok(!/fetch\(|XMLHttpRequest|WebSocket/.test(t), f + ' 외부 호출');
  });
  const m = /<script>([\s\S]*?)<\/script>/.exec(html);
  assert.doesNotThrow(() => new Function(m[1]));
  assert.ok(html.includes('try {') && html.includes('localStorage'));
});
