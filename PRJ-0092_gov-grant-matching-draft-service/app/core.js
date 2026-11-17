'use strict';
// 정부지원사업 공고 매칭·신청서 초안 계산기. 공고는 모두 직접 만든 가상 예시입니다.

var INDUSTRIES = ['음식점업', '도소매업', '제조업', '정보통신업', '서비스업', '농림어업'];
var REGIONS = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'];

function parseDate(s) {
  var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || '').trim());
  if (!m) return null;
  var y = +m[1], mo = +m[2], d = +m[3];
  var t = Date.UTC(y, mo - 1, d);
  var c = new Date(t);
  if (c.getUTCFullYear() !== y || c.getUTCMonth() !== mo - 1 || c.getUTCDate() !== d) return null;
  return Math.round(t / 86400000);
}

function daysLeft(deadline, today) {
  var a = parseDate(deadline), b = parseDate(today);
  if (a === null || b === null) return null;
  return a - b;
}

function dLabel(n) {
  if (n === null) return '날짜 확인 필요';
  if (n < 0) return '마감 지남';
  if (n === 0) return '오늘 마감';
  return 'D-' + n;
}

function num(v) {
  if (v === '' || v === null || v === undefined) return NaN;
  return Number(v);
}

function validateProfile(p) {
  var errs = [];
  if (!p || typeof p !== 'object') return ['사업자 조건이 없습니다.'];
  if (!p.industry || INDUSTRIES.indexOf(p.industry) < 0) errs.push('업종을 골라 주세요.');
  var by = num(p.bizYears), em = num(p.employees), ra = num(p.repAge);
  if (!isFinite(by) || by < 0) errs.push('업력은 0 이상 숫자로 적어 주세요. (예비 창업자는 0)');
  if (!p.region || REGIONS.indexOf(p.region) < 0) errs.push('지역을 골라 주세요.');
  if (!isFinite(em) || em < 0 || Math.floor(em) !== em) errs.push('직원 수는 0 이상 정수로 적어 주세요.');
  if (!isFinite(ra) || ra < 15 || ra > 100 || Math.floor(ra) !== ra) errs.push('대표 나이는 15~100 사이 정수로 적어 주세요.');
  if (parseDate(p.today) === null) errs.push('오늘 날짜는 YYYY-MM-DD 형식으로 적어 주세요.');
  return errs;
}

// 한 공고에 대한 판정. 경계값은 모두 "이상/이하"(포함)입니다.
function evaluate(profile, grant) {
  var reasons = [], matched = [];
  var n = daysLeft(grant.deadline, profile.today);
  var by = num(profile.bizYears), em = num(profile.employees), ra = num(profile.repAge);

  function chk(ok, okMsg, badMsg) { if (ok) matched.push(okMsg); else reasons.push(badMsg); }

  if (grant.industries && grant.industries.length) {
    chk(grant.industries.indexOf(profile.industry) >= 0,
      '업종 일치 (' + profile.industry + ')',
      '업종 불일치: 공고 대상은 ' + grant.industries.join('·') + ', 내 업종은 ' + profile.industry);
  }
  if (grant.minBizYears !== undefined) {
    chk(by >= grant.minBizYears, '업력 ' + by + '년 (최소 ' + grant.minBizYears + '년 충족)',
      '업력 부족: 최소 ' + grant.minBizYears + '년 필요, 내 업력 ' + by + '년');
  }
  if (grant.maxBizYears !== undefined) {
    chk(by <= grant.maxBizYears, '업력 ' + by + '년 (최대 ' + grant.maxBizYears + '년 이내)',
      '업력 초과: 최대 ' + grant.maxBizYears + '년까지, 내 업력 ' + by + '년');
  }
  if (grant.regions && grant.regions.length) {
    chk(grant.regions.indexOf(profile.region) >= 0, '지역 일치 (' + profile.region + ')',
      '지역 불일치: 공고 대상은 ' + grant.regions.join('·') + ', 내 지역은 ' + profile.region);
  }
  if (grant.minEmployees !== undefined) {
    chk(em >= grant.minEmployees, '직원 ' + em + '명 (최소 ' + grant.minEmployees + '명 충족)',
      '직원 수 부족: 최소 ' + grant.minEmployees + '명 필요, 현재 ' + em + '명');
  }
  if (grant.maxEmployees !== undefined) {
    chk(em <= grant.maxEmployees, '직원 ' + em + '명 (최대 ' + grant.maxEmployees + '명 이내)',
      '직원 수 초과: 최대 ' + grant.maxEmployees + '명까지, 현재 ' + em + '명');
  }
  if (grant.minRepAge !== undefined) {
    chk(ra >= grant.minRepAge, '대표 나이 ' + ra + '세 (최소 ' + grant.minRepAge + '세 충족)',
      '대표 나이 미달: ' + grant.minRepAge + '세 이상 대상, 현재 ' + ra + '세');
  }
  if (grant.maxRepAge !== undefined) {
    chk(ra <= grant.maxRepAge, '대표 나이 ' + ra + '세 (' + grant.maxRepAge + '세 이하 충족)',
      '대표 나이 초과: ' + grant.maxRepAge + '세 이하 대상, 현재 ' + ra + '세');
  }

  var closed = n === null || n < 0;
  if (closed) reasons.push(n === null ? '마감일을 읽을 수 없음' : '마감일(' + grant.deadline + ')이 지났음');
  var status = closed ? 'closed' : (reasons.length ? 'ineligible' : 'eligible');
  return { id: grant.id, grant: grant, status: status, daysLeft: n, dLabel: dLabel(n),
    reasons: reasons, matched: matched, urgent: !closed && n <= 7 };
}

var ORDER = { eligible: 0, ineligible: 1, closed: 2 };

// 자격 일치 먼저, 그 안에서 마감 임박순. 같은 날이면 공고 번호순.
function rank(profile, grants) {
  var errs = validateProfile(profile);
  if (errs.length) return { errors: errs, results: [] };
  var res = grants.map(function (g) { return evaluate(profile, g); });
  res.sort(function (a, b) {
    if (ORDER[a.status] !== ORDER[b.status]) return ORDER[a.status] - ORDER[b.status];
    if (a.status === 'closed') {
      var x = a.daysLeft === null ? -Infinity : a.daysLeft, y = b.daysLeft === null ? -Infinity : b.daysLeft;
      if (x !== y) return y - x; // 최근에 끝난 것 먼저
    } else if (a.daysLeft !== b.daysLeft) return a.daysLeft - b.daysLeft;
    return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  });
  return { errors: [], results: res };
}

function summarize(results) {
  var s = { eligible: 0, ineligible: 0, closed: 0, urgent: 0 };
  results.forEach(function (r) { s[r.status]++; if (r.status === 'eligible' && r.urgent) s.urgent++; });
  return s;
}

function won(man) { return String(Math.round(man)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '만 원'; }

// 신청서 초안(문단 틀). 빈칸은 [  ]로 남겨 직접 채우게 합니다.
function draftApplication(profile, grant) {
  var errs = validateProfile(profile);
  if (errs.length) return { errors: errs, title: '', paragraphs: [] };
  if (!grant) return { errors: ['공고를 선택해 주세요.'], title: '', paragraphs: [] };
  var ev = evaluate(profile, grant);
  var biz = profile.industry + ' 분야 ' + profile.region + ' 소재 사업체(업력 ' + profile.bizYears + '년, 직원 ' + profile.employees + '명)';
  var paras = [
    { head: '1. 신청 개요', body: '본 사업체는 [상호명]으로, ' + biz + '입니다. 대표자 [성명]은 「' + grant.name + '」(' + grant.agency + ')에 신청하고자 합니다.' },
    { head: '2. 신청 자격 충족 사유', body: ev.matched.length ? ev.matched.map(function (m) { return '- ' + m; }).join('\n') : '- [충족 사유를 적어 주세요]' },
    { head: '3. 신청 동기와 필요성', body: '[현재 겪는 어려움 1~2가지]를 해결하기 위해 본 사업의 지원 분야(' + grant.focus + ')가 필요합니다. [근거가 되는 매출·고객 수 등 숫자]를 함께 적습니다.' },
    { head: '4. 사업 추진 계획', body: '[1단계: 시기와 할 일] → [2단계: 시기와 할 일] → [3단계: 시기와 할 일]. 최대 지원 규모는 ' + won(grant.amount) + '이며 계획은 그 범위 안에서 세웁니다.' },
    { head: '5. 지원금 사용 계획', body: '[항목 1] [금액]원, [항목 2] [금액]원, [항목 3] [금액]원. 합계는 지원 한도 ' + won(grant.amount) + ' 이내로 맞춥니다.' },
    { head: '6. 기대 효과', body: '지원 후 [매출·고용·비용 절감 등 목표 수치]를 [시기]까지 달성하겠습니다.' },
    { head: '7. 제출 전 확인', body: '마감일 ' + grant.deadline + '(' + ev.dLabel + '). 제출 서류와 자격은 실제 공고문 원문으로 다시 확인합니다.' }
  ];
  var warn = ev.status === 'eligible' ? '' : (ev.status === 'closed' ? '이 공고는 마감되어 초안만 참고용입니다.' : '자격 불일치 사유가 있어 신청이 어려울 수 있습니다: ' + ev.reasons.join(' / '));
  return { errors: [], title: grant.name + ' 신청서 초안', warning: warn, paragraphs: paras,
    text: toText({ title: grant.name + ' 신청서 초안', paragraphs: paras }) };
}

function toText(d) {
  return '[' + d.title + ']\n\n' + d.paragraphs.map(function (p) { return p.head + '\n' + p.body; }).join('\n\n') + '\n';
}

// 직접 만든 가상 예시 공고입니다. 실제 공고가 아닙니다.
var SAMPLE_GRANTS = [
  { id: 'G01', name: '(예시) 동네 음식점 위생 개선 지원', agency: '가상시청 경제과', industries: ['음식점업'], regions: ['서울', '경기', '인천'],
    maxBizYears: 7, maxEmployees: 9, deadline: '2026-11-20', amount: 500, focus: '주방 위생·설비 개선' },
  { id: 'G02', name: '(예시) 청년 대표 첫걸음 창업 자금', agency: '가상창업진흥원', industries: [], regions: [],
    maxBizYears: 3, minRepAge: 19, maxRepAge: 39, deadline: '2026-12-05', amount: 3000, focus: '청년 창업 초기 자금' },
  { id: 'G03', name: '(예시) 소공인 스마트 장비 도입', agency: '가상중소벤처청', industries: ['제조업'], regions: [],
    minBizYears: 1, minEmployees: 2, maxEmployees: 9, deadline: '2026-11-30', amount: 2000, focus: '스마트 장비 도입' },
  { id: 'G04', name: '(예시) 소상공인 온라인 판로 개척', agency: '가상소상공인지원센터', industries: ['도소매업', '음식점업', '서비스업'], regions: [],
    maxEmployees: 4, deadline: '2026-12-15', amount: 300, focus: '온라인 판매 채널 구축' },
  { id: 'G05', name: '(예시) 지역 농가 가공 창업 지원', agency: '가상도청 농정과', industries: ['농림어업'], regions: ['강원', '충북', '충남', '전북', '전남', '경북', '경남'],
    deadline: '2026-11-25', amount: 1500, focus: '농산물 가공 시설' },
  { id: 'G06', name: '(예시) 중장년 재도약 컨설팅', agency: '가상고용센터', industries: [], regions: [],
    minRepAge: 40, minBizYears: 3, deadline: '2026-11-17', amount: 400, focus: '경영 컨설팅' },
  { id: 'G07', name: '(예시) 소프트웨어 초기기업 바우처', agency: '가상정보진흥원', industries: ['정보통신업'], regions: [],
    maxBizYears: 5, deadline: '2026-11-10', amount: 1000, focus: '개발·마케팅 바우처' }
];

var SAMPLE_PROFILE = { industry: '음식점업', bizYears: 2, region: '서울', employees: 3, repAge: 34, today: '2026-11-17' };

var api = { INDUSTRIES: INDUSTRIES, REGIONS: REGIONS, parseDate: parseDate, daysLeft: daysLeft, dLabel: dLabel,
  validateProfile: validateProfile, evaluate: evaluate, rank: rank, summarize: summarize, won: won,
  draftApplication: draftApplication, toText: toText, SAMPLE_GRANTS: SAMPLE_GRANTS, SAMPLE_PROFILE: SAMPLE_PROFILE };
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
