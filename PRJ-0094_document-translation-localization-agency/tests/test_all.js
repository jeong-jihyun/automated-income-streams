'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../app/core.js');

const H = 'ht' + 'tp'; // 시험 글에 쓸 주소 조각
const types = (r) => r.issues.map(i => i.type);

test('문단 나누기: 빈 줄 / --- 구분 / 빈 문단', () => {
  assert.deepStrictEqual(C.splitParagraphs('가\n\n나\n\n\n다', 'blank'), ['가', '나', '다']);
  assert.deepStrictEqual(C.splitParagraphs('가\n---\n\n---\n다', 'dash'), ['가', '', '다']);
  assert.deepStrictEqual(C.splitParagraphs('   ', 'blank'), []);
  assert.ok(C.hasDashSeparator('a\n---\nb'));
  assert.ok(!C.hasDashSeparator('a\nb'));
});
test('용어집 읽기: 주석·여러 번역어·잘못된 줄', () => {
  const g = C.parseGlossary('# 주석\nplan=요금제|플랜\n엉터리\n=값\n');
  assert.strictEqual(g.entries.length, 1);
  assert.deepStrictEqual(g.entries[0].alts, ['요금제', '플랜']);
  assert.strictEqual(g.errors.length, 2);
});
test('용어 찾기는 영문 단어 경계를 지킨다', () => {
  assert.ok(C.containsTerm('The Basic plan.', 'plan'));
  assert.ok(!C.containsTerm('We are planning', 'plan'));
  assert.ok(C.containsTerm('요금제를 고르세요', '요금제'));
});
test('날짜 뽑기: 여러 표기와 연도 없는 날짜', () => {
  const d = C.extractDates('On March 5, 2026 and 2026-03-06, 7월 8일, 15 Aug 2025.').dates;
  assert.strictEqual(d.length, 4);
  assert.ok(d.some(x => x.y === 2026 && x.m === 3 && x.d === 5));
  assert.ok(d.some(x => x.y === null && x.m === 7 && x.d === 8));
  assert.ok(d.some(x => x.y === 2025 && x.m === 8 && x.d === 15));
});
test('숫자 뽑기: 쉼표·소수·만 단위', () => {
  assert.deepStrictEqual(C.extractNumbers('1,000 and 2.50 and 3'), ['1000', '2.5', '3']);
  assert.deepStrictEqual(C.extractNumbers('1만 원, 2 million'), ['10000', '2000000']);
});
test('주소 뽑기: 끝 문장부호는 뺀다', () => {
  const u = C.extractUrls('See ' + H + 's://a.example/x, and www.b.example.').urls;
  assert.deepStrictEqual(u, [H + 's://a.example/x', 'www.b.example']);
});
test('고유명사 후보: 문장 첫 단어는 빼고 연속 대문자는 하나로', () => {
  assert.deepStrictEqual(C.extractProperNouns('Our CEO, Maria Lopez, will present at the Seoul office.'), ['CEO', 'Maria Lopez', 'Seoul']);
  assert.deepStrictEqual(C.extractProperNouns('The report is ready. Hello there.'), []);
});
test('샘플: 의도한 문제들이 모두 잡힌다', () => {
  const r = C.checkTranslation(C.SAMPLE_SRC, C.SAMPLE_TGT, C.SAMPLE_GLOSSARY);
  for (const t of ['date', 'url', 'number', 'glossary', 'proper', 'empty', 'ratio']) assert.ok(types(r).includes(t), t + ' 없음');
  assert.strictEqual(r.srcCount, 6);
  assert.strictEqual(r.tgtCount, 6);
  assert.strictEqual(r.errors + r.warnings, r.issues.length);
  assert.ok(!r.issues.some(i => i.para === 6), '깨끗한 6번 문단에 문제가 나옴');
});
test('깨끗한 번역은 문제 없음', () => {
  const src = 'The Basic plan costs $29 per month. Visit www.acme.example/pricing today.\n\nSee you on 2026-03-05.';
  const tgt = '베이직 요금제는 월 $29입니다. 오늘 www.acme.example/pricing 을 방문하세요.\n\n2026년 3월 5일에 만나요.';
  const r = C.checkTranslation(src, tgt, 'Basic=베이직\nplan=요금제');
  assert.deepStrictEqual(r.issues, []);
});
test('문단 수 불일치', () => {
  const r = C.checkTranslation('하나\n\n둘\n\n셋', '일\n\n이', '');
  assert.strictEqual(r.issues[0].type, 'count');
  assert.strictEqual(r.paired, 2);
});
test('빈 번역문·자리표시 번역문', () => {
  const r = C.checkTranslation('Hello world\n---\nGood luck\n---\nBye now', '안녕\n---\nTODO\n---\n', '');
  assert.deepStrictEqual(r.issues.filter(i => i.type === 'empty').map(i => i.para), [2, 3]);
});
test('날짜: 연도 없는 쪽은 월·일만 비교, 다르면 오류', () => {
  assert.deepStrictEqual(types(C.checkTranslation('Due on March 5, 2026.', '3월 5일까지입니다.', '')), []);
  assert.ok(types(C.checkTranslation('Due on March 5, 2026.', '3월 6일까지입니다.', '')).includes('date'));
});
test('숫자: 쉼표 표기 차이는 통과, 값이 다르면 오류', () => {
  assert.deepStrictEqual(types(C.checkTranslation('It costs 1,000 dollars.', '비용은 1000달러입니다.', '')), []);
  assert.ok(types(C.checkTranslation('It costs 1,000 dollars.', '비용은 100달러입니다.', '')).includes('number'));
});
test('주소: 달라진 주소를 잡고 www/끝 슬래시 차이는 봐준다', () => {
  assert.ok(types(C.checkTranslation('Go to ' + H + 's://a.example/x now', '지금 ' + H + 's://a.example/y 로 가세요', '')).includes('url'));
  assert.deepStrictEqual(types(C.checkTranslation('Go to ' + H + 's://www.a.example/x/ now', '지금 ' + H + 's://a.example/x 로 가세요', '')), []);
});
test('용어집 위반과 여러 번역어 허용', () => {
  assert.ok(types(C.checkTranslation('Open the dashboard.', '화면을 여세요.', 'dashboard=대시보드')).includes('glossary'));
  assert.deepStrictEqual(types(C.checkTranslation('Open the dashboard.', '대시보드를 여세요.', 'dashboard=대시보드')), []);
  assert.deepStrictEqual(types(C.checkTranslation('Open the dashboard.', '계기판을 여세요.', 'dashboard=대시보드|계기판')), []);
});
test('길이 비율: 너무 짧음/김, 아주 짧은 원문은 건너뜀', () => {
  const long = 'This sentence is deliberately long enough to test the ratio rule.';
  assert.ok(types(C.checkTranslation(long, '짧다', '')).includes('ratio'));
  assert.ok(types(C.checkTranslation(long, '가'.repeat(400), '')).includes('ratio'));
  assert.deepStrictEqual(types(C.checkTranslation('Hi', '안녕하세요 반갑습니다 여러분', '')), []);
});
test('단어 수 세기', () => {
  assert.strictEqual(C.countWords('Hello brave world 한국어 문장'), 5);
  assert.strictEqual(C.countWords('日本語'), 3);
  assert.strictEqual(C.countWords('  \n - '), 0);
});
test('견적 기본 계산', () => {
  const q = C.quote({ words: 1000, ratePerWord: 30, reviewPerWord: 20, reReviewPerWord: 10, formatFee: 30000 });
  assert.strictEqual(q.supply, 90000);
  assert.strictEqual(q.vat, 9000);
  assert.strictEqual(q.total, 99000);
  assert.strictEqual(q.items.length, 4);
});
test('돈 합계 보존: 항목 합 = 총합 (여러 값)', () => {
  for (const w of [0, 1, 7, 333, 1234, 98765]) for (const r of [0, 12.5, 33, 77.7]) for (const v of [0, 9.9, 20]) for (const f of [0, 1, 999, 30001]) {
    const q = C.quote({ words: w, ratePerWord: r, reviewPerWord: v, reReviewPerWord: r / 3, formatFee: f });
    assert.strictEqual(q.items.reduce((a, i) => a + i.supply, 0), q.supply);
    assert.strictEqual(q.items.reduce((a, i) => a + i.vat, 0), q.vat);
    assert.strictEqual(q.items.reduce((a, i) => a + i.total, 0), q.total);
    assert.strictEqual(q.supply + q.vat, q.total);
    q.items.forEach(i => assert.ok(Number.isInteger(i.vat) && i.vat >= 0));
  }
});
test('allocate는 합을 정확히 보존', () => {
  assert.strictEqual(C.allocate([1, 1, 1], 10).reduce((x, y) => x + y, 0), 10);
  assert.deepStrictEqual(C.allocate([0, 0], 5), [0, 0]);
});
test('이상한 견적 입력은 0으로', () => {
  assert.strictEqual(C.quote({ words: -5, ratePerWord: 'abc', reviewPerWord: null, reReviewPerWord: undefined, formatFee: -1 }).total, 0);
});
test('화면 파일: http 글자 없음, viewport, core.js 사용, 필요한 칸·스크립트 문법', () => {
  const dir = path.join(__dirname, '..', 'app');
  const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.ok(html.includes('name="viewport"'));
  assert.ok(html.includes('src="core.js"'));
  for (const f of ['index.html', 'core.js', 'style.css']) {
    assert.ok(!/http/i.test(fs.readFileSync(path.join(dir, f), 'utf8')), f + ' 에 http 글자');
  }
  for (const id of ['src', 'tgt', 'gloss', 'runCheck', 'checkOut', 'runQuote', 'quoteOut', 'words', 'rate', 'review', 'rereview', 'fmt', 'resetAll']) {
    assert.ok(html.includes('id="' + id + '"'), id + ' 칸 없음');
  }
  const m = /<script>([\s\S]*?)<\/script>/.exec(html);
  assert.doesNotThrow(() => new Function(m[1]));
  assert.ok(/try\s*\{[^}]*localStorage/.test(html));
});
