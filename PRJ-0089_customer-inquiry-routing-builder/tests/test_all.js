'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const C = require('../app/core.js');
const R = C.DEFAULT_RULES;

test('여러 줄 나누기: 빈 줄과 번호 제거', () => {
  assert.deepStrictEqual(C.splitInquiries('1. 배송 문의\n\n  - 환불해요  \r\n2) 결제'), ['배송 문의', '환불해요', '결제']);
  assert.deepStrictEqual(C.splitInquiries(''), []);
  assert.deepStrictEqual(C.splitInquiries(null), []);
});

test('분류: 배송', () => assert.strictEqual(C.classify('택배 송장 번호가 안 떠요', R).team, '배송'));
test('분류: 환불·교환', () => assert.strictEqual(C.classify('환불하고 싶어요', R).team, '환불·교환'));
test('분류: 결제', () => assert.strictEqual(C.classify('카드 이중결제 됐어요', R).team, '결제'));
test('분류: 사용법', () => assert.strictEqual(C.classify('로그인 비밀번호 어떻게 바꿔요', R).team, '사용법'));

test('분류: 키워드 없으면 기타', () => {
  const r = C.classify('영업시간이 몇 시까지인가요?', R);
  assert.strictEqual(r.team, C.OTHER_TEAM);
  assert.deepStrictEqual(r.hits, []);
});

test('분류: 더 많이 맞은 칸이 이기고, 동점이면 앞 규칙', () => {
  assert.strictEqual(C.classify('배송이 늦어서 환불 반품 원해요', R).team, '환불·교환');
  assert.strictEqual(C.classify('교환 방법 알려주세요', R).team, '환불·교환');
});

test('분류: 대소문자·공백 무시', () => {
  const rules = [{ team: '영문', keywords: ['Refund'] }];
  assert.strictEqual(C.classify('please   REFUND me', rules).team, '영문');
});

test('긴급도: 평범한 문장은 보통 0점', () => {
  const u = C.urgency('택배 언제 오나요?');
  assert.strictEqual(u.score, 0); assert.strictEqual(u.level, '보통');
});
test('긴급도: 기한 표현 하나면 주의', () => {
  const u = C.urgency('오늘까지 답 주세요');
  assert.strictEqual(u.score, 3); assert.strictEqual(u.level, '주의');
});
test('긴급도: 화남+기한+느낌표는 긴급', () => {
  const u = C.urgency('너무 화가 나요. 오늘까지 안 되면 신고할게요!!');
  assert.ok(u.score >= 5); assert.strictEqual(u.level, '긴급');
  assert.ok(u.reasons.length >= 3);
});
test('긴급도: 점수 상한(같은 종류 많이 써도 무한히 늘지 않음)', () => {
  const u = C.urgency('화나 짜증 최악 어이없 황당 열받 불쾌');
  assert.strictEqual(u.score, 6);
});
test('긴급도: 사용자 기준 바꾸기', () => {
  const cfg = C.clone(C.DEFAULT_URGENCY); cfg.urgentAt = 3;
  assert.strictEqual(C.urgency('오늘까지 주세요', cfg).level, '긴급');
});

test('일괄 처리와 요약', () => {
  const items = C.processBatch(C.SAMPLE_TEXT, R, C.DEFAULT_URGENCY);
  assert.strictEqual(items.length, 8);
  const s = C.summarize(items);
  assert.strictEqual(s.total, 8);
  assert.strictEqual(s.urgent + s.caution + s.normal, 8);
  assert.ok(s.urgent >= 1);
  assert.ok(s.unassigned >= 1);
});

test('칸별 묶기: 칸 순서는 규칙 순서, 기타는 맨 뒤, 칸 안은 긴급 순', () => {
  const items = C.processBatch('환불 해주세요\n환불 오늘까지 해주세요 화가 나요!!\n영업시간?\n택배 언제요', R, C.DEFAULT_URGENCY);
  const g = C.groupByTeam(items, R);
  assert.deepStrictEqual(g.map(x => x.team), ['배송', '환불·교환', C.OTHER_TEAM]);
  const ref = g[1];
  assert.strictEqual(ref.items.length, 2);
  assert.ok(ref.items[0].score > ref.items[1].score);
  assert.strictEqual(ref.urgentCount, 1);
});

test('칸별 묶기: 동점은 입력 순서 유지', () => {
  const g = C.groupByTeam(C.processBatch('환불 A\n환불 B\n환불 C', R, C.DEFAULT_URGENCY), R);
  assert.deepStrictEqual(g[0].items.map(i => i.text), ['환불 A', '환불 B', '환불 C']);
});

test('규칙 글 <-> 규칙 왕복', () => {
  const back = C.parseRules(C.rulesToText(R));
  assert.deepStrictEqual(back.errors, []);
  assert.deepStrictEqual(back.rules, R);
});

test('규칙 글 오류: 콜론 없음, 키워드 없음, 칸 이름 중복', () => {
  const r = C.parseRules('콜론없음\n배송:\n결제: 카드\n결제: 입금');
  assert.strictEqual(r.rules.length, 1);
  assert.strictEqual(r.errors.length, 3);
});

test('규칙 글: 전각 콜론·쉼표와 빈 줄 허용', () => {
  const r = C.parseRules('\n배송：택배，송장\n');
  assert.deepStrictEqual(r.rules, [{ team: '배송', keywords: ['택배', '송장'] }]);
});

test('규칙을 바꾸면 분류가 바뀐다', () => {
  const r = C.parseRules('영업: 영업시간, 운영');
  assert.strictEqual(C.classify('영업시간 알려주세요', r.rules).team, '영업');
});

test('긴급도 단어 글 왕복과 오류', () => {
  const back = C.parseUrgency(C.urgencyToText(C.DEFAULT_URGENCY));
  assert.deepStrictEqual(back.errors, []);
  assert.deepStrictEqual(back.cfg.angry, C.DEFAULT_URGENCY.angry);
  assert.strictEqual(C.parseUrgency('엉뚱: 가').errors.length, 1);
});

test('복사용 글', () => {
  const g = C.groupByTeam(C.processBatch('환불 오늘까지 화가 나요!!', R, C.DEFAULT_URGENCY), R);
  const t = C.toPlainText(g);
  assert.ok(t.includes('[환불·교환] 1건'));
  assert.ok(t.includes('(긴급)'));
});

test('앱 파일: 외부 주소·서버 호출 없음', () => {
  for (const f of ['index.html', 'core.js', 'style.css']) {
    const s = fs.readFileSync(path.join(__dirname, '..', 'app', f), 'utf8');
    assert.ok(!/https?:\/\//i.test(s), f + ' 에 http 주소가 있어요');
    assert.ok(!/\b(fetch|XMLHttpRequest|WebSocket|sendBeacon)\b/.test(s), f + ' 에 네트워크 호출이 있어요');
  }
  const html = fs.readFileSync(path.join(__dirname, '..', 'app', 'index.html'), 'utf8');
  assert.ok(/name="viewport"/.test(html));
  assert.ok(/<html lang="ko">/.test(html));
});

test('화면 스크립트: 가짜 화면에서 첫 실행·버튼 동작', () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'app', 'index.html'), 'utf8');
  const code = /<script>([\s\S]*?)<\/script>/.exec(html)[1];
  const els = {};
  function mk(id) {
    const e = { id, value: '', className: '', style: {}, children: [], handlers: {}, _t: '',
      get textContent() { return this._t; },
      set textContent(v) { this._t = v; this.children = []; },
      appendChild(c) { this.children.push(c); return c; },
      addEventListener(t, f) { this.handlers[t] = f; } };
    return e;
  }
  const doc = {
    getElementById(id) { return els[id] || (els[id] = mk(id)); },
    createElement(t) { const e = mk(''); e.tag = t; return e; },
    createTextNode(t) { return { text: t }; }
  };
  const store = {};
  const ctx = { window: { InquiryCore: C }, document: doc,
    localStorage: { getItem: k => store[k] || null, setItem: (k, v) => { store[k] = v; } } };
  vm.runInNewContext(code, ctx);
  assert.ok(els.inq.value.includes('택배'));
  assert.ok(els.plain.value.includes('[배송]'));
  assert.strictEqual(els.groups.children.length, 5);
  assert.ok(store['prj0089-state-v1']);
  // 입력을 바꿔 다시 분류
  els.inq.value = '환불해 주세요'; els.run.handlers.click();
  assert.strictEqual(els.groups.children.length, 1);
  // 잘못된 규칙이면 오류 글
  els.rules.value = '이상한줄'; els.run.handlers.click();
  assert.ok(els.msg.textContent.length > 0);
  // 되돌리기
  els.reset.handlers.click();
  assert.strictEqual(els.msg.textContent, '');
});

test('저장소가 막혀 있어도 화면이 뜬다', () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'app', 'index.html'), 'utf8');
  const code = /<script>([\s\S]*?)<\/script>/.exec(html)[1];
  const els = {};
  const mk = id => ({ id, value: '', textContent: '', style: {}, children: [], handlers: {},
    appendChild(c) { return c; }, addEventListener(t, f) { this.handlers[t] = f; } });
  const doc = { getElementById: id => els[id] || (els[id] = mk(id)), createElement: () => mk(''), createTextNode: t => ({ text: t }) };
  const boom = () => { throw new Error('blocked'); };
  vm.runInNewContext(code, { window: { InquiryCore: C }, document: doc, localStorage: { getItem: boom, setItem: boom } });
  assert.ok(els.plain.value.includes('[배송]'));
});
