'use strict';
// 핵심 계산·판정. 화면(index.html)은 이 파일을 불러 쓴다. 기기 시계는 읽지 않는다(오늘 값은 입력으로 받음).

var SOON_DAYS = 30;
var NOTICE_DAYS = [60, 30, 7];
var VAT_RATE = 0.1;

// 'YYYY-MM-DD' -> UTC 자정 밀리초. 잘못된 날짜(2026-02-30 등)는 null.
function parseDate(s) {
  var m = /^\s*(\d{4})-(\d{2})-(\d{2})\s*$/.exec(String(s == null ? '' : s));
  if (!m) return null;
  var y = +m[1], mo = +m[2], d = +m[3];
  var t = Date.UTC(y, mo - 1, d);
  var c = new Date(t);
  if (c.getUTCFullYear() !== y || c.getUTCMonth() !== mo - 1 || c.getUTCDate() !== d) return null;
  return t;
}
function formatDate(t) {
  var c = new Date(t), p = function (n, w) { return String(n).padStart(w, '0'); };
  return p(c.getUTCFullYear(), 4) + '-' + p(c.getUTCMonth() + 1, 2) + '-' + p(c.getUTCDate(), 2);
}
function daysBetween(fromT, toT) { return Math.round((toT - fromT) / 86400000); }
function addDays(t, n) { return t + n * 86400000; }
// 달 더하기. 말일을 넘으면 그 달 말일로 맞춘다(1/31 + 1달 = 2/28 또는 29).
function addMonths(t, n) {
  var c = new Date(t), y = c.getUTCFullYear(), m = c.getUTCMonth() + n, d = c.getUTCDate();
  var last = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
  return Date.UTC(y, m, Math.min(d, last));
}

// ---- (1) 라이선스 키 검사 ----
// 형식: 접두어(영대문자 2~8자)-연도4자리-일련번호4자리-검사값4자리
// 검사값 = (접두어·연도·일련번호 글자 코드의 단순 합계) % 10000, 4자리 0 채움. 암호 보안이 아니다.
function keyChecksum(prefix, year, seq) {
  var s = String(prefix) + String(year) + String(seq), sum = 0;
  for (var i = 0; i < s.length; i++) sum += s.charCodeAt(i);
  return String(sum % 10000).padStart(4, '0');
}
function makeKey(prefix, year, seq) {
  var y = String(year), q = String(seq).padStart(4, '0');
  return prefix + '-' + y + '-' + q + '-' + keyChecksum(prefix, y, q);
}
function parseKey(key) {
  var m = /^([A-Z]{2,8})-(\d{4})-(\d{4})-(\d{4})$/.exec(String(key == null ? '' : key).trim());
  if (!m) return { ok: false, reason: '형식이 맞지 않습니다. 예: ACME-2026-0001-0xxx (영대문자-연도-번호-검사값 4자리)' };
  var want = keyChecksum(m[1], m[2], m[3]);
  if (m[4] !== want) return { ok: false, reason: '검사값이 맞지 않습니다(단순 합계 규칙). 이 키의 검사값은 ' + want + ' 이어야 합니다.' };
  return { ok: true, prefix: m[1], year: m[2], seq: m[3], check: m[4] };
}

// 판정 우선순위: 형식 오류 > 입력 오류 > 만료 > 좌석 초과 > 만료 임박 > 유효
function checkLicense(input) {
  var today = parseDate(input.today), exp = parseDate(input.expiry);
  var allowed = Number(input.seatsAllowed), used = Number(input.seatsUsed);
  var k = parseKey(input.key);
  if (!k.ok) return { status: 'format', label: '형식 오류', message: k.reason, daysLeft: null, flags: ['format'] };
  var errs = [];
  if (today === null) errs.push('오늘 날짜(YYYY-MM-DD)가 올바르지 않습니다.');
  if (exp === null) errs.push('만료일(YYYY-MM-DD)이 올바르지 않습니다.');
  if (!(Number.isInteger(allowed) && allowed >= 0)) errs.push('허용 좌석 수는 0 이상의 정수여야 합니다.');
  if (!(Number.isInteger(used) && used >= 0)) errs.push('사용 중 좌석 수는 0 이상의 정수여야 합니다.');
  if (errs.length) return { status: 'input', label: '입력 오류', message: errs.join(' '), daysLeft: null, flags: ['input'] };
  var daysLeft = daysBetween(today, exp);
  var flags = [];
  if (daysLeft < 0) flags.push('expired');
  if (used > allowed) flags.push('seats');
  if (daysLeft >= 0 && daysLeft <= SOON_DAYS) flags.push('soon');
  var status = flags.indexOf('expired') >= 0 ? 'expired' : flags.indexOf('seats') >= 0 ? 'seats' : flags.indexOf('soon') >= 0 ? 'soon' : 'valid';
  var labels = { expired: '만료', seats: '좌석 초과', soon: '만료 임박', valid: '유효' };
  var msg;
  if (status === 'expired') msg = '만료일(' + input.expiry + ')이 ' + (-daysLeft) + '일 지났습니다.';
  else if (status === 'seats') msg = '허용 ' + allowed + '석인데 ' + used + '석을 쓰고 있어 ' + (used - allowed) + '석 초과입니다.';
  else if (status === 'soon') msg = daysLeft === 0 ? '오늘이 만료일입니다(오늘까지 유효).' : '만료까지 ' + daysLeft + '일 남았습니다.';
  else msg = '만료까지 ' + daysLeft + '일, 좌석 ' + used + '/' + allowed + ' 사용 중입니다.';
  if (status === 'expired' && flags.indexOf('seats') >= 0) msg += ' 좌석도 ' + (used - allowed) + '석 초과입니다.';
  if (status === 'seats' && flags.indexOf('soon') >= 0) msg += ' 만료도 ' + daysLeft + '일 남았습니다.';
  return { status: status, label: labels[status], message: msg, daysLeft: daysLeft, flags: flags };
}

// ---- (2) 연간 라이선스 견적 ----
// 합이 정확히 total이 되도록 가장 큰 나머지 순서로 나눔(정수)
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

// 예시 단가(실제 가격 아님). 구간별 누진: 해당 구간에 걸친 좌석에만 그 구간 단가를 적용한다.
var SEAT_TIERS = [
  { from: 1, to: 10, price: 120000 },
  { from: 11, to: 50, price: 100000 },
  { from: 51, to: Infinity, price: 80000 }
];
var SUPPORT = { basic: { name: '기본(이메일, 영업일 3일)', fee: 0 }, standard: { name: '표준(영업일 1일)', fee: 600000 }, premium: { name: '프리미엄(4시간, 전담)', fee: 1800000 } };
var MULTI_DISCOUNT = { 1: 0, 2: 0.05, 3: 0.1 };

function quote(input) {
  var seats = Number(input.seats), years = Number(input.years);
  if (!(Number.isInteger(seats) && seats >= 1)) return { error: '좌석 수는 1 이상의 정수여야 합니다.' };
  if (!MULTI_DISCOUNT.hasOwnProperty(years)) return { error: '계약 기간은 1, 2, 3년 중에서 고릅니다.' };
  var sup = SUPPORT[input.support];
  if (!sup) return { error: '지원 등급을 고르세요.' };
  var tierLines = [], perYearLicense = 0;
  SEAT_TIERS.forEach(function (t) {
    var n = Math.max(0, Math.min(seats, t.to) - t.from + 1);
    if (n > 0) { tierLines.push({ from: t.from, to: Math.min(seats, t.to), seats: n, price: t.price, amount: n * t.price }); perYearLicense += n * t.price; }
  });
  var licenseGross = perYearLicense * years;
  var supportGross = sup.fee * years;
  var gross = licenseGross + supportGross;
  var rate = MULTI_DISCOUNT[years];
  var discount = Math.round(gross * rate);
  var dparts = allocate([licenseGross, supportGross], discount);
  var licenseNet = licenseGross - dparts[0], supportNet = supportGross - dparts[1];
  var supply = licenseNet + supportNet;
  var vat = Math.round(supply * VAT_RATE);
  var vparts = allocate([licenseNet, supportNet], vat);
  return {
    seats: seats, years: years, supportName: sup.name, tierLines: tierLines,
    perYearLicense: perYearLicense, discountRate: rate, discount: discount,
    items: [
      { name: '라이선스 사용료(' + years + '년, 할인 반영)', supply: licenseNet, vat: vparts[0], total: licenseNet + vparts[0] },
      { name: '지원 추가금(' + years + '년, 할인 반영)', supply: supportNet, vat: vparts[1], total: supportNet + vparts[1] }
    ],
    gross: gross, supply: supply, vat: vat, total: supply + vat
  };
}

// ---- (3) 갱신 일정 ----
// 계약 종료일 = 시작일 + 개월 수 - 1일. 안내일 = 종료일 - 60/30/7일.
function renewalSchedule(input) {
  var start = parseDate(input.start), today = parseDate(input.today);
  var years = Number(input.years);
  if (start === null) return { error: '계약 시작일(YYYY-MM-DD)이 올바르지 않습니다.' };
  if (today === null) return { error: '오늘 날짜(YYYY-MM-DD)가 올바르지 않습니다.' };
  if (!(Number.isInteger(years) && years >= 1 && years <= 10)) return { error: '계약 기간은 1~10년의 정수여야 합니다.' };
  var end = addDays(addMonths(start, years * 12), -1);
  var rows = NOTICE_DAYS.map(function (n) {
    var t = addDays(end, -n), diff = daysBetween(today, t);
    return { before: n, date: formatDate(t), daysFromToday: diff, state: diff < 0 ? 'past' : diff === 0 ? 'today' : 'upcoming' };
  });
  return { start: formatDate(start), end: formatDate(end), daysToEnd: daysBetween(today, end), notices: rows };
}

function won(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; }

var SAMPLE_KEY = makeKey('ACME', 2026, 1);
var SAMPLE_TODAY = '2026-11-17';

var api = { parseDate: parseDate, formatDate: formatDate, daysBetween: daysBetween, addDays: addDays, addMonths: addMonths,
  keyChecksum: keyChecksum, makeKey: makeKey, parseKey: parseKey, checkLicense: checkLicense,
  allocate: allocate, quote: quote, renewalSchedule: renewalSchedule, won: won,
  SEAT_TIERS: SEAT_TIERS, SUPPORT: SUPPORT, MULTI_DISCOUNT: MULTI_DISCOUNT, SOON_DAYS: SOON_DAYS, NOTICE_DAYS: NOTICE_DAYS,
  SAMPLE_KEY: SAMPLE_KEY, SAMPLE_TODAY: SAMPLE_TODAY };
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
