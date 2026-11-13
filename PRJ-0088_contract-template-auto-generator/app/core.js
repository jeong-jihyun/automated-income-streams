'use strict';
/* 계약서·서류 템플릿 자동 생성 - 핵심 계산·판정 (법률 자문 아님) */

var DISCLAIMER = '이 문서는 연습·참고용 초안이며 법률 자문이 아닙니다. 실제 사용 전 전문가 확인이 필요합니다.';

var DIGITS = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
var SMALL = ['', '십', '백', '천'];
var BIG = ['', '만', '억', '조'];

/* 숫자 -> 한글 금액 (예: 3500000 -> 삼백오십만). 0 -> 영. 계약서식으로 '일십', '일백'처럼 1을 생략하지 않음 */
function moneyToHangul(n) {
  if (typeof n !== 'number' || !isFinite(n) || n < 0 || Math.floor(n) !== n || n > 9999999999999999) return null;
  if (n === 0) return '영';
  var s = String(n);
  var groups = [];
  for (var e = s.length; e > 0; e -= 4) groups.unshift(s.slice(Math.max(0, e - 4), e));
  var out = '';
  for (var gi = 0; gi < groups.length; gi++) {
    var g = groups[gi];
    var bigIdx = groups.length - 1 - gi;
    var part = '';
    for (var i = 0; i < g.length; i++) {
      var d = Number(g[i]);
      if (d === 0) continue;
      part += DIGITS[d] + SMALL[g.length - 1 - i];
    }
    if (part) out += part + BIG[bigIdx];
  }
  return out;
}

/* '1,234,000' 또는 '1234000원' -> 1234000. 잘못되면 null */
function parseMoney(str) {
  if (str === null || str === undefined) return null;
  var t = String(str).replace(/[,\s원₩]/g, '');
  if (!/^\d+$/.test(t)) return null;
  var n = Number(t);
  if (!isFinite(n) || n > 9999999999999999) return null;
  return n;
}

function formatWon(n) {
  if (typeof n !== 'number' || !isFinite(n)) return '';
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/* 'YYYY-MM-DD' -> 비교용 숫자(20261201). 존재하지 않는 날짜는 null */
function parseDate(str) {
  if (typeof str !== 'string') return null;
  var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(str.trim());
  if (!m) return null;
  var y = Number(m[1]), mo = Number(m[2]), d = Number(m[3]);
  var dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
  return y * 10000 + mo * 100 + d;
}

function formatDate(str) {
  var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(str || '').trim());
  if (!m || parseDate(str) === null) return '';
  return Number(m[1]) + '년 ' + Number(m[2]) + '월 ' + Number(m[3]) + '일';
}

/* 총액을 비율(%)로 나눔. 마지막 칸이 나머지를 받아 합계가 항상 총액과 같다 */
function splitPayment(total, percents) {
  if (typeof total !== 'number' || total < 0 || Math.floor(total) !== total) return null;
  if (!Array.isArray(percents) || percents.length === 0) return null;
  var sum = 0, i;
  for (i = 0; i < percents.length; i++) {
    if (typeof percents[i] !== 'number' || percents[i] < 0) return null;
    sum += percents[i];
  }
  if (sum !== 100) return null;
  var parts = [], used = 0;
  for (i = 0; i < percents.length - 1; i++) {
    var p = Math.floor(total * percents[i] / 100);
    parts.push(p);
    used += p;
  }
  parts.push(total - used);
  return parts;
}

/* ---------- 템플릿 ---------- */
var TEMPLATES = [
  {
    id: 'service',
    name: '용역 계약서',
    fields: [
      { key: '갑', label: '갑(발주자) 이름', type: 'text', required: true },
      { key: '을', label: '을(수행자) 이름', type: 'text', required: true },
      { key: '용역명', label: '용역 내용', type: 'text', required: true },
      { key: '계약일', label: '계약일', type: 'date', required: true },
      { key: '시작일', label: '용역 시작일', type: 'date', required: true },
      { key: '종료일', label: '용역 종료일', type: 'date', required: true },
      { key: '총액', label: '총 대금(원)', type: 'money', required: true },
      { key: '계약금', label: '계약금(원)', type: 'money', required: true, allowZero: true },
      { key: '중도금', label: '중도금(원)', type: 'money', required: true, allowZero: true },
      { key: '잔금', label: '잔금(원)', type: 'money', required: true, allowZero: true },
      { key: '잔금일', label: '잔금 지급일', type: 'date', required: true },
      { key: '총액한글입력', label: '총 대금 한글(선택, 직접 쓰면 맞는지 확인)', type: 'text', required: false, hangulOf: '총액' },
      { key: '특약', label: '특약 사항(선택)', type: 'textarea', required: false }
    ],
    body:
      '용 역 계 약 서\n\n' +
      '{{갑}}(이하 "갑")과 {{을}}(이하 "을")은 아래와 같이 용역 계약을 체결한다.\n\n' +
      '제1조 (용역의 내용) 을은 갑에게 "{{용역명}}" 용역을 제공한다.\n' +
      '제2조 (기간) 용역 기간은 {{시작일}}부터 {{종료일}}까지로 한다.\n' +
      '제3조 (대금) 총 대금은 일금 {{총액_한글}}원정(₩{{총액}})으로 한다.\n' +
      '  1. 계약금: {{계약금}}원 (일금 {{계약금_한글}}원정)\n' +
      '  2. 중도금: {{중도금}}원 (일금 {{중도금_한글}}원정)\n' +
      '  3. 잔금: {{잔금}}원 (일금 {{잔금_한글}}원정), {{잔금일}}까지 지급한다.\n' +
      '제4조 (특약) {{특약}}\n\n' +
      '위 계약의 성립을 증명하기 위하여 계약서 2통을 작성하여 갑과 을이 서명 또는 날인한 후 각 1통씩 보관한다.\n\n' +
      '계약일: {{계약일}}\n갑: {{갑}} (서명 또는 인)\n을: {{을}} (서명 또는 인)',
    rules: function (v, add) {
      var t = v.total, a = v.num['계약금'], b = v.num['중도금'], c = v.num['잔금'];
      if (t !== null && a !== null && b !== null && c !== null && a + b + c !== t) {
        var diff = (a + b + c) - t;
        add('error', '계약금+중도금+잔금(' + formatWon(a + b + c) + '원)이 총 대금(' + formatWon(t) + '원)과 ' +
          formatWon(Math.abs(diff)) + '원 ' + (diff > 0 ? '많습니다' : '모자랍니다') + '.');
      }
      var d = v.date;
      if (d['계약일'] !== null && d['시작일'] !== null && d['계약일'] > d['시작일']) add('error', '계약일이 용역 시작일보다 늦습니다.');
      if (d['시작일'] !== null && d['종료일'] !== null && d['시작일'] > d['종료일']) add('error', '용역 시작일이 종료일보다 늦습니다.');
      if (d['계약일'] !== null && d['잔금일'] !== null && d['잔금일'] < d['계약일']) add('error', '잔금 지급일이 계약일보다 빠릅니다.');
      if (d['종료일'] !== null && d['잔금일'] !== null && d['잔금일'] < d['종료일'] && d['잔금일'] >= (d['계약일'] || 0)) add('warn', '잔금 지급일이 용역 종료일보다 빠릅니다. 의도한 것인지 확인하세요.');
      if (v.raw['갑'] && v.raw['을'] && v.raw['갑'].trim() === v.raw['을'].trim()) add('warn', '갑과 을의 이름이 같습니다.');
    }
  },
  {
    id: 'lease',
    name: '임대차 계약서',
    fields: [
      { key: '임대인', label: '임대인(집주인) 이름', type: 'text', required: true },
      { key: '임차인', label: '임차인(세입자) 이름', type: 'text', required: true },
      { key: '소재지', label: '임대 대상 소재지', type: 'text', required: true },
      { key: '계약일', label: '계약일', type: 'date', required: true },
      { key: '시작일', label: '임대 시작일', type: 'date', required: true },
      { key: '종료일', label: '임대 종료일', type: 'date', required: true },
      { key: '보증금', label: '보증금(원)', type: 'money', required: true },
      { key: '월세', label: '월세(원)', type: 'money', required: true, allowZero: true },
      { key: '월세일', label: '월세 내는 날(매월 며칠)', type: 'number', required: true, min: 1, max: 31 },
      { key: '보증금한글입력', label: '보증금 한글(선택, 직접 쓰면 맞는지 확인)', type: 'text', required: false, hangulOf: '보증금' },
      { key: '특약', label: '특약 사항(선택)', type: 'textarea', required: false }
    ],
    body:
      '임 대 차 계 약 서\n\n' +
      '임대인 {{임대인}}과 임차인 {{임차인}}은 아래 부동산에 관하여 임대차 계약을 체결한다.\n\n' +
      '제1조 (대상) 소재지: {{소재지}}\n' +
      '제2조 (보증금) 보증금은 일금 {{보증금_한글}}원정(₩{{보증금}})으로 한다.\n' +
      '제3조 (월세) 월세는 일금 {{월세_한글}}원정(₩{{월세}})으로 하고, 매월 {{월세일}}일에 지급한다.\n' +
      '제4조 (기간) 임대 기간은 {{시작일}}부터 {{종료일}}까지로 한다.\n' +
      '제5조 (특약) {{특약}}\n\n' +
      '위 계약의 성립을 증명하기 위하여 계약서 2통을 작성하여 임대인과 임차인이 서명 또는 날인한 후 각 1통씩 보관한다.\n\n' +
      '계약일: {{계약일}}\n임대인: {{임대인}} (서명 또는 인)\n임차인: {{임차인}} (서명 또는 인)',
    rules: function (v, add) {
      var d = v.date;
      if (d['계약일'] !== null && d['시작일'] !== null && d['계약일'] > d['시작일']) add('error', '계약일이 임대 시작일보다 늦습니다.');
      if (d['시작일'] !== null && d['종료일'] !== null && d['시작일'] >= d['종료일']) add('error', '임대 시작일이 종료일과 같거나 늦습니다.');
      if (v.num['월세'] === 0) add('warn', '월세가 0원입니다. 전세 계약이 맞는지 확인하세요.');
      if (v.raw['임대인'] && v.raw['임차인'] && v.raw['임대인'].trim() === v.raw['임차인'].trim()) add('warn', '임대인과 임차인의 이름이 같습니다.');
    }
  },
  {
    id: 'loan',
    name: '차용증',
    fields: [
      { key: '채권자', label: '빌려준 사람(채권자)', type: 'text', required: true },
      { key: '채무자', label: '빌린 사람(채무자)', type: 'text', required: true },
      { key: '금액', label: '빌린 금액(원)', type: 'money', required: true },
      { key: '차용일', label: '빌린 날', type: 'date', required: true },
      { key: '변제일', label: '갚기로 한 날', type: 'date', required: true },
      { key: '이자율', label: '연 이자율(%)', type: 'number', required: true, min: 0, max: 100 },
      { key: '금액한글입력', label: '금액 한글(선택, 직접 쓰면 맞는지 확인)', type: 'text', required: false, hangulOf: '금액' }
    ],
    body:
      '차 용 증\n\n' +
      '채무자 {{채무자}}은 채권자 {{채권자}}으로부터 아래와 같이 금전을 차용하였음을 확인한다.\n\n' +
      '1. 차용 금액: 일금 {{금액_한글}}원정(₩{{금액}})\n' +
      '2. 차용일: {{차용일}}\n' +
      '3. 변제일: {{변제일}}\n' +
      '4. 이자: 연 {{이자율}}%\n\n' +
      '채무자는 위 금액을 변제일까지 채권자에게 갚겠다.\n\n' +
      '작성일: {{차용일}}\n채무자: {{채무자}} (서명 또는 인)\n채권자: {{채권자}} (확인)',
    rules: function (v, add) {
      var d = v.date;
      if (d['차용일'] !== null && d['변제일'] !== null && d['차용일'] > d['변제일']) add('error', '변제일이 차용일보다 빠릅니다.');
      var r = v.num['이자율'];
      if (r !== null && r > 20) add('warn', '연 이자율이 20%를 넘습니다. 법에서 정한 최고 이자율 제한이 있을 수 있으니 확인하세요.');
      if (v.raw['채권자'] && v.raw['채무자'] && v.raw['채권자'].trim() === v.raw['채무자'].trim()) add('warn', '채권자와 채무자의 이름이 같습니다.');
    }
  }
];

var SAMPLES = {
  service: {
    '갑': '김하늘', '을': '이바다', '용역명': '쇼핑몰 웹사이트 디자인', '계약일': '2026-12-01', '시작일': '2026-12-05',
    '종료일': '2027-01-31', '총액': '3000000', '계약금': '900000', '중도금': '900000', '잔금': '1200000',
    '잔금일': '2027-02-10', '총액한글입력': '삼백만', '특약': '수정 요청은 2회까지 무상으로 한다.'
  },
  lease: {
    '임대인': '박산', '임차인': '최강', '소재지': '서울특별시 예시구 예시로 12, 301호', '계약일': '2026-12-01',
    '시작일': '2027-01-01', '종료일': '2028-12-31', '보증금': '20000000', '월세': '600000', '월세일': '25',
    '보증금한글입력': '', '특약': '반려동물은 사전에 협의한다.'
  },
  loan: {
    '채권자': '정서연', '채무자': '한도윤', '금액': '5000000', '차용일': '2026-12-01', '변제일': '2027-06-30',
    '이자율': '5', '금액한글입력': ''
  }
};

function getTemplate(id) {
  for (var i = 0; i < TEMPLATES.length; i++) if (TEMPLATES[i].id === id) return TEMPLATES[i];
  return null;
}

function sampleValues(id) {
  var s = SAMPLES[id];
  if (!s) return {};
  var o = {};
  for (var k in s) o[k] = s[k];
  return o;
}

function emptyValues(id) {
  var tpl = getTemplate(id), o = {};
  if (!tpl) return o;
  for (var i = 0; i < tpl.fields.length; i++) o[tpl.fields[i].key] = '';
  return o;
}

function isBlank(s) { return s === undefined || s === null || String(s).trim() === ''; }

/* 값 해석: raw / 숫자 / 날짜 */
function analyze(tpl, values) {
  var v = { raw: {}, num: {}, date: {}, total: null };
  for (var i = 0; i < tpl.fields.length; i++) {
    var f = tpl.fields[i];
    var raw = values[f.key];
    v.raw[f.key] = isBlank(raw) ? '' : String(raw);
    if (f.type === 'money') v.num[f.key] = isBlank(raw) ? null : parseMoney(raw);
    else if (f.type === 'number') {
      var t = isBlank(raw) ? null : Number(String(raw).trim());
      v.num[f.key] = (t === null || !isFinite(t)) ? null : t;
    } else if (f.type === 'date') v.date[f.key] = isBlank(raw) ? null : parseDate(raw);
  }
  v.total = v.num['총액'] !== undefined ? v.num['총액'] : null;
  return v;
}

/* 점검: {missing:[라벨], errors:[글], warnings:[글], ok:boolean} */
function validate(tpl, values) {
  var res = { missing: [], errors: [], warnings: [], ok: false };
  var v = analyze(tpl, values);
  function add(level, msg) { (level === 'error' ? res.errors : res.warnings).push(msg); }
  for (var i = 0; i < tpl.fields.length; i++) {
    var f = tpl.fields[i];
    var raw = v.raw[f.key];
    if (raw === '') {
      if (f.required) res.missing.push(f.label);
      continue;
    }
    if (f.type === 'money') {
      var n = v.num[f.key];
      if (n === null) add('error', '"' + f.label + '"은(는) 숫자만 써야 합니다.');
      else if (n === 0 && !f.allowZero) add('error', '"' + f.label + '"은(는) 0보다 커야 합니다.');
    } else if (f.type === 'number') {
      var x = v.num[f.key];
      if (x === null) add('error', '"' + f.label + '"은(는) 숫자만 써야 합니다.');
      else if ((f.min !== undefined && x < f.min) || (f.max !== undefined && x > f.max)) add('error', '"' + f.label + '"은(는) ' + f.min + '~' + f.max + ' 사이여야 합니다.');
      else if (f.key === '월세일' && Math.floor(x) !== x) add('error', '"' + f.label + '"은(는) 정수여야 합니다.');
    } else if (f.type === 'date') {
      if (v.date[f.key] === null) add('error', '"' + f.label + '"이(가) 올바른 날짜가 아닙니다. (예: 2026-12-01)');
    } else if (f.hangulOf) {
      var target = v.num[f.hangulOf];
      if (target !== null && target !== undefined) {
        if (!hangulMatches(target, raw)) add('error', '직접 쓴 한글 금액("' + raw.trim() + '")이 숫자(' + formatWon(target) + '원 = ' + moneyToHangul(target) + ')와 다릅니다.');
      }
    }
  }
  /* 날짜·금액이 잘못된 칸이 있으면 순서 점검은 건너뛴 값(null)으로 자동 처리 */
  tpl.rules(v, add);
  res.ok = res.missing.length === 0 && res.errors.length === 0;
  return res;
}

/* 직접 쓴 한글 금액 비교: 공백·'일금'·'원'·'정' 제거 후 비교. '삼백만' = '삼백만원정' */
function normHangul(s) {
  return String(s).replace(/\s/g, '').replace(/^일금/, '').replace(/원?정?$/, '');
}
function hangulMatches(n, typed) {
  var want = moneyToHangul(n);
  if (want === null) return false;
  var a = normHangul(typed);
  if (a === want) return true;
  /* 1을 생략한 표기('십','백','만')도 허용 */
  var alt = want.replace(/일(?=[십백천])/g, '');
  var alt2 = alt.replace(/^일(?=[만억조])/, '');
  return a === alt || a === alt2;
}

/* 본문 만들기: 빈칸은 【○○ 입력 필요】로 표시 */
function render(tpl, values) {
  var v = analyze(tpl, values);
  var byKey = {};
  for (var i = 0; i < tpl.fields.length; i++) byKey[tpl.fields[i].key] = tpl.fields[i];
  var text = tpl.body.replace(/\{\{([^}]+)\}\}/g, function (all, key) {
    key = key.trim();
    var hangulKey = /_한글$/.test(key) ? key.slice(0, -3) : null;
    if (hangulKey) {
      var hn = v.num[hangulKey];
      if (hn === null || hn === undefined) return '【' + (byKey[hangulKey] ? byKey[hangulKey].label : hangulKey) + ' 입력 필요】';
      return moneyToHangul(hn);
    }
    var f = byKey[key];
    if (!f) return all;
    var raw = v.raw[key];
    if (raw === '') {
      if (!f.required) return '(없음)';
      return '【' + f.label + ' 입력 필요】';
    }
    if (f.type === 'money') return v.num[key] === null ? '【' + f.label + ' 확인 필요】' : formatWon(v.num[key]);
    if (f.type === 'date') { var fd = formatDate(raw); return fd || '【' + f.label + ' 확인 필요】'; }
    return raw.trim();
  });
  return text;
}

function hangulPreview(tpl, values) {
  var v = analyze(tpl, values), out = [];
  for (var i = 0; i < tpl.fields.length; i++) {
    var f = tpl.fields[i];
    if (f.type === 'money' && v.num[f.key] !== null && v.num[f.key] !== undefined) {
      out.push({ label: f.label, won: formatWon(v.num[f.key]), hangul: moneyToHangul(v.num[f.key]) });
    }
  }
  return out;
}

/* 한 번에: 문서 + 점검 + 한글 표기 */
function build(id, values) {
  var tpl = getTemplate(id);
  if (!tpl) return null;
  var check = validate(tpl, values);
  return { template: tpl.name, text: render(tpl, values), check: check, hangul: hangulPreview(tpl, values), disclaimer: DISCLAIMER };
}

var api = {
  DISCLAIMER: DISCLAIMER, TEMPLATES: TEMPLATES, moneyToHangul: moneyToHangul, parseMoney: parseMoney, formatWon: formatWon,
  parseDate: parseDate, formatDate: formatDate, splitPayment: splitPayment, getTemplate: getTemplate, sampleValues: sampleValues,
  emptyValues: emptyValues, validate: validate, render: render, hangulPreview: hangulPreview, build: build, hangulMatches: hangulMatches
};
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
