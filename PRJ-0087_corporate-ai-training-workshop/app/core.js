'use strict';
// 기업 AI 업무 활용 교육: 견적·손익분기 계산 + AI 활용 체크리스트 점수. 외부 연결 없음.

var SAMPLE = {
  instructorFee: 800000, // 강사료(고정)
  venueFee: 300000,      // 장소비(고정)
  materialPerPerson: 15000, // 1인 자료비
  headcount: 20,
  pricePerPerson: 90000
};

var CHECK_ITEMS = [
  { id: 'mail', label: '메일·공지 초안을 AI로 쓴다' },
  { id: 'minutes', label: '회의록을 AI로 요약한다' },
  { id: 'report', label: '보고서 목차·초안을 AI로 만든다' },
  { id: 'sheet', label: '엑셀 수식·정리를 AI에게 묻는다' },
  { id: 'translate', label: '번역·문장 다듬기에 AI를 쓴다' },
  { id: 'rule', label: '넣으면 안 되는 정보(개인정보·기밀) 규칙을 안다' },
  { id: 'check', label: 'AI 답을 사람이 다시 확인한다' }
];
// 각 항목 답: 0=안 함, 1=가끔, 2=자주
var CHECK_SAMPLE = { mail: 2, minutes: 1, report: 1, sheet: 0, translate: 2, rule: 1, check: 2 };

function toInt(v) {
  var t = String(v === null || v === undefined ? '' : v).replace(/[,\s원명]/g, '');
  if (t === '') return NaN;
  var n = Number(t);
  if (!isFinite(n)) return NaN;
  return Math.round(n);
}

// 입력 검증. 문제 목록(한국어)을 돌려준다.
function validate(inp) {
  var errs = [];
  var f = [['instructorFee', '강사료'], ['venueFee', '장소비'], ['materialPerPerson', '1인 자료비'], ['pricePerPerson', '1인 참가비']];
  f.forEach(function (p) {
    var n = toInt(inp[p[0]]);
    if (isNaN(n)) errs.push(p[1] + '은(는) 숫자로 넣어 주세요.');
    else if (n < 0) errs.push(p[1] + '은(는) 0 이상이어야 해요.');
  });
  var h = toInt(inp.headcount);
  if (isNaN(h) || h < 1) errs.push('인원은 1명 이상 숫자로 넣어 주세요.');
  else if (h > 10000) errs.push('인원은 10000명 이하로 넣어 주세요.');
  return errs;
}

// 총액 total(원, 정수)을 n명에게 나눈다. 나머지는 앞사람부터 1원씩 더해서 합이 정확히 total.
function splitCost(total, n) {
  total = Math.round(total); n = Math.round(n);
  if (!(n >= 1)) throw new Error('n은 1 이상이어야 해요');
  var base = Math.floor(total / n), rem = total - base * n, out = [];
  for (var i = 0; i < n; i++) out.push(base + (i < rem ? 1 : 0));
  return out;
}

// 인원 n명일 때 손익
function scenario(inp, n) {
  var fixed = toInt(inp.instructorFee) + toInt(inp.venueFee);
  var mat = toInt(inp.materialPerPerson), price = toInt(inp.pricePerPerson);
  var cost = fixed + mat * n, revenue = price * n;
  return { n: n, cost: cost, revenue: revenue, profit: revenue - cost };
}

// 손익분기 인원: 매출 >= 비용 이 되는 가장 작은 인원. 1인당 남는 돈(참가비-자료비)이 0 이하면 null.
function breakEven(inp) {
  var fixed = toInt(inp.instructorFee) + toInt(inp.venueFee);
  var margin = toInt(inp.pricePerPerson) - toInt(inp.materialPerPerson);
  if (margin <= 0) return null;
  if (fixed === 0) return 1;
  return Math.max(1, Math.ceil(fixed / margin));
}

function calcWorkshop(inp) {
  var errs = validate(inp);
  if (errs.length) return { ok: false, errors: errs };
  var n = toInt(inp.headcount);
  var cur = scenario(inp, n);
  var be = breakEven(inp);
  var shares = splitCost(cur.cost, n);
  var maxN = Math.max(n, be || 0, 10);
  maxN = Math.min(maxN + 5, 200);
  var table = [];
  var step = maxN > 40 ? Math.ceil(maxN / 20) : 1;
  for (var k = 1; k <= maxN; k += step) table.push(scenario(inp, k));
  if (table[table.length - 1].n !== maxN) table.push(scenario(inp, maxN));
  var verdict;
  if (be === null) verdict = '참가비가 1인 자료비보다 낮거나 같아서, 인원이 늘어도 고정비를 못 메워요. 참가비를 올려 보세요.';
  else if (cur.profit >= 0) verdict = n + '명이면 ' + cur.profit + '원 남아요. (손익분기 ' + be + '명)';
  else verdict = n + '명이면 ' + (-cur.profit) + '원 모자라요. ' + be + '명부터 흑자예요.';
  return {
    ok: true, headcount: n, totalCost: cur.cost, revenue: cur.revenue, profit: cur.profit,
    breakEven: be, perPersonCost: shares, perPersonMin: Math.min.apply(null, shares),
    perPersonMax: Math.max.apply(null, shares), shareSum: shares.reduce(function (a, b) { return a + b; }, 0),
    table: table, verdict: verdict
  };
}

// 체크리스트 점수: 항목당 0~2, 만점 대비 백분율(정수).
function scoreChecklist(answers) {
  var total = 0, max = CHECK_ITEMS.length * 2, missing = [];
  CHECK_ITEMS.forEach(function (it) {
    var v = answers ? answers[it.id] : undefined;
    v = Number(v);
    if (v !== 0 && v !== 1 && v !== 2) { v = 0; }
    total += v;
    if (v === 0) missing.push(it.label);
  });
  var pct = Math.round(total / max * 100);
  var level, advice;
  if (pct >= 75) { level = '활용 잘함'; advice = '이미 잘 쓰고 있어요. 안 하는 항목부터 한 가지씩 늘려 보세요.'; }
  else if (pct >= 40) { level = '활용 중'; advice = '기본은 되어 있어요. 아래 "안 하는 업무"를 교육 주제로 잡으면 좋아요.'; }
  else { level = '시작 단계'; advice = '메일·회의록 요약처럼 쉬운 업무부터 시작하는 교육이 알맞아요.'; }
  return { score: total, max: max, percent: pct, level: level, advice: advice, notUsed: missing };
}

var CORE = { SAMPLE: SAMPLE, CHECK_ITEMS: CHECK_ITEMS, CHECK_SAMPLE: CHECK_SAMPLE, toInt: toInt, validate: validate,
  splitCost: splitCost, scenario: scenario, breakEven: breakEven, calcWorkshop: calcWorkshop, scoreChecklist: scoreChecklist };
if (typeof module !== 'undefined') module.exports = CORE;
if (typeof window !== 'undefined') window.CORE = CORE;
