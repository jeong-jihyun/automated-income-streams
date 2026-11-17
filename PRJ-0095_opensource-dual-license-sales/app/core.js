'use strict';
// 오픈소스 이중 라이선스 판매 - 핵심 계산. 법률 자문 아님, 구간·단가는 예시값.
var DEFAULT_TIERS = '9,100000\n49,300000\n249,800000\n999,2000000';
var DEFAULT_TIERS_TEXT = DEFAULT_TIERS;

function num(v, def) {
  if (v === '' || v === null || v === undefined) return def;
  var n = Number(v);
  return isFinite(n) ? n : NaN;
}

// "최대 직원 수,개발자 1명 연 단가" 줄들을 읽는다. 오름차순이어야 한다.
function parseTiers(text) {
  var tiers = [], errors = [];
  String(text || '').split(/\r?\n/).forEach(function (line, idx) {
    line = line.trim();
    if (!line) return;
    var p = line.split(',');
    var max = Number(p[0]), unit = Number(p[1]);
    if (p.length !== 2 || !isFinite(max) || !isFinite(unit) || max < 1 || unit < 0 || Math.floor(max) !== max || Math.floor(unit) !== unit) {
      errors.push((idx + 1) + '번째 줄을 읽을 수 없습니다: ' + line);
      return;
    }
    tiers.push({ max: max, unit: unit });
  });
  for (var i = 1; i < tiers.length; i++) {
    if (tiers[i].max <= tiers[i - 1].max) { errors.push('구간의 직원 수는 앞 줄보다 커야 합니다.'); break; }
  }
  if (!tiers.length && !errors.length) errors.push('구간이 하나도 없습니다.');
  return { tiers: tiers, errors: errors };
}

function tierFor(employees, tiers) {
  for (var i = 0; i < tiers.length; i++) if (employees <= tiers[i].max) return tiers[i];
  return null;
}

// 사용자 유형 판정. type: individual | nonprofit | company
function judge(inp) {
  var type = inp.type, saas = !!inp.saas;
  var emp = num(inp.employees, 0);
  var parsed = parseTiers(inp.tiersText === undefined ? DEFAULT_TIERS : inp.tiersText);
  if (['individual', 'nonprofit', 'company'].indexOf(type) < 0) return { verdict: 'inquiry', label: '문의 필요', reasons: ['사용자 유형을 고르세요.'], error: true };
  if (isNaN(emp) || emp < 0 || Math.floor(emp) !== emp) return { verdict: 'inquiry', label: '문의 필요', reasons: ['직원 수는 0 이상의 정수로 넣으세요.'], error: true };
  var reasons = [];
  if (saas) {
    reasons.push('내 서비스(SaaS)나 제품에 이 소프트웨어를 넣어 다시 배포·제공하면 일반 사용 범위를 벗어납니다.');
    reasons.push('재배포 조건은 사례마다 달라 개별 협의가 필요합니다.');
    return { verdict: 'inquiry', label: '문의 필요', reasons: reasons };
  }
  if (type === 'individual') {
    reasons.push('개인이 자기 용도로 쓰는 경우는 무료 범위입니다.');
    reasons.push('이 도구로 번 돈이 없는 경우를 기준으로 합니다. 돈을 받는 일에 쓰면 회사 유형으로 다시 판정하세요.');
    return { verdict: 'free', label: '무료 사용 가능', reasons: reasons };
  }
  if (type === 'nonprofit') {
    reasons.push('비영리 단체의 내부 사용은 무료 범위입니다.');
    reasons.push('단체가 이 소프트웨어로 영리 사업을 하면 회사 유형으로 다시 판정하세요.');
    return { verdict: 'free', label: '무료 사용 가능', reasons: reasons };
  }
  if (parsed.errors.length) return { verdict: 'inquiry', label: '문의 필요', reasons: parsed.errors, error: true };
  var t = tierFor(emp, parsed.tiers);
  if (!t) {
    reasons.push('직원 ' + emp + '명은 설정된 최대 구간(' + parsed.tiers[parsed.tiers.length - 1].max + '명)을 넘습니다.');
    reasons.push('대기업 규모는 개별 계약이 필요합니다.');
    return { verdict: 'inquiry', label: '문의 필요', reasons: reasons };
  }
  reasons.push('회사의 상업용 사용은 유료 라이선스가 필요합니다.');
  reasons.push('직원 ' + emp + '명은 "' + t.max + '명 이하" 구간(개발자 1명 연 ' + won(t.unit) + ')에 해당합니다.');
  return { verdict: 'paid', label: '유료 라이선스 필요', reasons: reasons, tier: t };
}

// 합계를 비율대로 나누되 항목 합이 항상 total이 되게 한다(가장 큰 나머지).
function allocate(amounts, total) {
  var sum = amounts.reduce(function (a, b) { return a + b; }, 0);
  if (sum <= 0) return amounts.map(function () { return 0; });
  var raw = amounts.map(function (a) { return a * total / sum; });
  var base = raw.map(Math.floor);
  var left = total - base.reduce(function (a, b) { return a + b; }, 0);
  var order = raw.map(function (r, i) { return { i: i, f: r - Math.floor(r) }; })
    .sort(function (a, b) { return b.f - a.f || a.i - b.i; });
  for (var k = 0; k < left; k++) base[order[k].i]++;
  return base;
}

// 견적: 개발자 수 x 연 단가 x 연수 - 다년 할인, 부가세 10%. 연도별 줄로 나눠도 합이 보존된다.
function quote(inp) {
  var emp = num(inp.employees, 0), devs = num(inp.devs, 0), years = num(inp.years, 1);
  var d2 = num(inp.disc2, 0), d3 = num(inp.disc3, 0);
  var bad = function (v) { return isNaN(v) || v < 0 || Math.floor(v) !== v; };
  if (bad(emp)) return { error: '직원 수는 0 이상의 정수로 넣으세요.' };
  if (bad(devs) || devs < 1) return { error: '개발자 수는 1 이상의 정수로 넣으세요.' };
  if (bad(years) || years < 1 || years > 10) return { error: '계약 연수는 1~10 사이의 정수로 넣으세요.' };
  if (isNaN(d2) || isNaN(d3) || d2 < 0 || d3 < 0 || d2 > 100 || d3 > 100) return { error: '할인율은 0~100 사이로 넣으세요.' };
  var parsed = parseTiers(inp.tiersText === undefined ? DEFAULT_TIERS : inp.tiersText);
  if (parsed.errors.length) return { error: parsed.errors.join(' ') };
  var t = tierFor(emp, parsed.tiers);
  if (!t) return { error: '직원 수가 최대 구간을 넘어 자동 견적을 낼 수 없습니다. 개별 문의가 필요합니다.' };
  var pct = years >= 3 ? d3 : (years === 2 ? d2 : 0);
  var gross = devs * t.unit * years;
  var discount = Math.round(gross * pct / 100);
  var supply = gross - discount;
  var vat = Math.round(supply * 0.1);
  var perYearBase = [];
  for (var i = 0; i < years; i++) perYearBase.push(1);
  var supplyParts = allocate(perYearBase, supply);
  var vatParts = allocate(supplyParts, vat);
  var items = supplyParts.map(function (s, i) {
    return { name: (i + 1) + '년차', supply: s, vat: vatParts[i], total: s + vatParts[i] };
  });
  return { tier: t, unit: t.unit, devs: devs, years: years, discountPct: pct, gross: gross, discount: discount,
    supply: supply, vat: vat, total: supply + vat, items: items };
}

// CLA(기여자 저작권 동의) 점검. 답: true/false
function claCheck(a) {
  var warnings = [], todos = [], blocked = false;
  if (a.external) {
    if (!a.claSigned) {
      blocked = true;
      warnings.push('경고: 외부 기여 코드가 있는데 모든 기여자의 CLA(저작권 양도 또는 재라이선스 허락) 서명이 없습니다. 이 상태로는 그 코드를 유료 라이선스로 다시 팔 권리가 없어 이중 라이선스가 불가능합니다.');
      todos.push('외부 기여자 모두에게 CLA 서명을 받거나, 그 코드를 걷어내 새로 쓰세요.');
    } else {
      todos.push('서명한 CLA 목록(이름·날짜·기여 범위)을 보관하세요.');
    }
    if (a.employer === false) {
      warnings.push('주의: 회사 소속 기여자는 회사의 허락이 없으면 CLA 서명이 효력이 없을 수 있습니다.');
      todos.push('회사 소속 기여자는 회사 명의의 CLA(법인용)를 받으세요.');
    }
  } else {
    todos.push('앞으로 외부 기여를 받기 전에 CLA 절차부터 만드세요.');
  }
  if (a.copyleftDep) {
    blocked = true;
    warnings.push('경고: GPL·AGPL 같은 카피레프트 의존 라이브러리를 포함하면 그 조건이 코드 전체에 번질 수 있어 유료 라이선스로 따로 팔기 어렵습니다.');
    todos.push('의존 라이브러리의 라이선스를 모두 확인하고, 카피레프트는 교체하세요.');
  }
  if (a.external && a.claSigned && !a.copyleftDep && a.employer !== false) {
    todos.push('모든 기여 코드의 출처(직접 작성 여부)를 한 번 더 확인하세요.');
  }
  var status = blocked ? 'blocked' : (warnings.length ? 'warn' : 'ok');
  var label = blocked ? '이중 라이선스 불가' : (warnings.length ? '주의가 필요함' : '이중 라이선스 가능성 있음');
  return { status: status, label: label, warnings: warnings, todos: todos };
}

function won(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; }

var api = { parseTiers: parseTiers, tierFor: tierFor, judge: judge, allocate: allocate, quote: quote,
  claCheck: claCheck, won: won, DEFAULT_TIERS_TEXT: DEFAULT_TIERS_TEXT };
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
