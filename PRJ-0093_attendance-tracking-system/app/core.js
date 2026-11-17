'use strict';
// 근태·출퇴근 집계 핵심 계산. 브라우저(window.Core)와 node(module.exports) 양쪽에서 쓴다.
// 기준값은 모두 예시이며 입력칸에서 바꿀 수 있다. 세법·노동법 자문이 아니다.

var DEFAULTS = {
  stdHours: 8,          // 소정 근로시간(시간)
  schedStart: '09:00',  // 소정 출근 시각(지각 판정 기준)
  schedEnd: '18:00',    // 소정 퇴근 시각(조퇴 판정 기준)
  graceMin: 0,          // 지각·조퇴 봐주는 분
  breakAt1: 4, breakMin1: 30,  // 4시간 이상이면 30분 휴게(예시)
  breakAt2: 8, breakMin2: 60,  // 8시간 이상이면 60분 휴게(예시)
  nightStart: 22, nightEnd: 6, // 야간 22시~06시(예시)
  otPremium: 0.5,       // 연장 가산 비율(예시)
  nightPremium: 0.5,    // 야간 가산 비율(예시)
  defaultWage: 10320,   // 기본 시급(원, 예시)
  month: ''             // 집계할 달(YYYY-MM), 비우면 전부
};

function num(v, d, min) {
  var n = Number(v);
  if (v === '' || v === null || v === undefined || !isFinite(n)) return d;
  return (min !== undefined && n < min) ? d : n;
}

function parseTime(s) {
  var m = /^(\d{1,2}):(\d{2})$/.exec(String(s).trim());
  if (!m) return null;
  var h = +m[1], mi = +m[2];
  if (h > 23 || mi > 59) return null;
  return h * 60 + mi;
}

function parseDate(s) {
  var m = /^(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})$/.exec(String(s).trim());
  if (!m) return null;
  var y = +m[1], mo = +m[2], d = +m[3];
  var dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
  return y + '-' + (mo < 10 ? '0' : '') + mo + '-' + (d < 10 ? '0' : '') + d;
}

function normalize(input) {
  var i = input || {}, D = DEFAULTS;
  var s = {
    stdHours: num(i.stdHours, D.stdHours, 0.1),
    schedStart: parseTime(i.schedStart) !== null ? i.schedStart : D.schedStart,
    schedEnd: parseTime(i.schedEnd) !== null ? i.schedEnd : D.schedEnd,
    graceMin: num(i.graceMin, D.graceMin, 0),
    breakAt1: num(i.breakAt1, D.breakAt1, 0), breakMin1: num(i.breakMin1, D.breakMin1, 0),
    breakAt2: num(i.breakAt2, D.breakAt2, 0), breakMin2: num(i.breakMin2, D.breakMin2, 0),
    nightStart: num(i.nightStart, D.nightStart, 0), nightEnd: num(i.nightEnd, D.nightEnd, 0),
    otPremium: num(i.otPremium, D.otPremium, 0), nightPremium: num(i.nightPremium, D.nightPremium, 0),
    defaultWage: Math.round(num(i.defaultWage, D.defaultWage, 0)),
    month: String(i.month === undefined || i.month === null ? '' : i.month).trim()
  };
  if (s.nightStart > 24) s.nightStart = D.nightStart;
  if (s.nightEnd > 24) s.nightEnd = D.nightEnd;
  return s;
}

// 줄마다 "이름 날짜 출근 퇴근". 모르는 시각은 - 로 쓴다. # 로 시작하는 줄은 건너뜀.
function parseRecords(text) {
  var records = [], errors = [];
  String(text || '').split(/\r?\n/).forEach(function (raw, idx) {
    var line = raw.trim();
    if (!line || line.charAt(0) === '#') return;
    var t = line.split(/[\s,;]+/).filter(function (x) { return x; });
    var ln = idx + 1;
    if (t.length !== 4) { errors.push(ln + '번째 줄: "이름 날짜 출근 퇴근" 4칸이어야 합니다 (' + line + ')'); return; }
    var date = parseDate(t[1]);
    if (!date) { errors.push(ln + '번째 줄: 날짜를 읽을 수 없습니다 (' + t[1] + ')'); return; }
    var ins = t[2], outs = t[3], a = null, b = null;
    var miss = /^(-|없음|\?)$/;
    if (!miss.test(ins)) { a = parseTime(ins); if (a === null) { errors.push(ln + '번째 줄: 출근 시각을 읽을 수 없습니다 (' + ins + ')'); return; } }
    if (!miss.test(outs)) { b = parseTime(outs); if (b === null) { errors.push(ln + '번째 줄: 퇴근 시각을 읽을 수 없습니다 (' + outs + ')'); return; } }
    if (a !== null && b !== null && a === b) { errors.push(ln + '번째 줄: 출근과 퇴근 시각이 같습니다 (' + line + ')'); return; }
    records.push({ line: ln, name: t[0], date: date, inMin: a, outMin: b });
  });
  return { records: records, errors: errors };
}

// "이름=시급" 또는 "이름 시급" 줄들
function parseWages(text) {
  var map = {}, errors = [];
  String(text || '').split(/\r?\n/).forEach(function (raw, idx) {
    var line = raw.trim();
    if (!line || line.charAt(0) === '#') return;
    var m = /^(\S+?)\s*[=:\s]\s*([\d,]+)\s*원?$/.exec(line);
    if (!m) { errors.push('시급 ' + (idx + 1) + '번째 줄을 읽을 수 없습니다 (' + line + ')'); return; }
    map[m[1]] = parseInt(m[2].replace(/,/g, ''), 10);
  });
  return { map: map, errors: errors };
}

// 구간 [a,b) 와 야간 시간대가 겹치는 분
function nightOverlap(a, b, ns, ne) {
  var s = Math.round(ns * 60), e = Math.round(ne * 60), total = 0, w = [], k;
  if (s === e) return 0;
  if (s > e) { for (k = -1; k <= 1; k++) w.push([k * 1440 + s, (k + 1) * 1440 + e]); }
  else { for (k = 0; k <= 1; k++) w.push([k * 1440 + s, k * 1440 + e]); }
  w.forEach(function (x) { total += Math.max(0, Math.min(b, x[1]) - Math.max(a, x[0])); });
  return total;
}

// 하루 계산. 퇴근이 출근보다 이르거나 같으면 다음 날로 본다(자정 넘김).
function calcDay(rec, settings) {
  var s = normalize(settings);
  var out = { missing: null, grossMin: 0, breakMin: 0, workMin: 0, otMin: 0, nightMin: 0, lateMin: 0, earlyMin: 0 };
  if (rec.inMin === null && rec.outMin === null) { out.missing = 'both'; return out; }
  if (rec.inMin === null) { out.missing = 'in'; return out; }
  if (rec.outMin === null) { out.missing = 'out'; return out; }
  var a = rec.inMin, b = rec.outMin;
  if (b <= a) b += 1440;
  var gross = b - a;
  var br = gross >= s.breakAt2 * 60 ? s.breakMin2 : (gross >= s.breakAt1 * 60 ? s.breakMin1 : 0);
  br = Math.min(br, gross);
  var work = gross - br;
  out.grossMin = gross; out.breakMin = br; out.workMin = work;
  out.otMin = Math.max(0, work - Math.round(s.stdHours * 60));
  out.nightMin = Math.min(work, nightOverlap(a, b, s.nightStart, s.nightEnd));
  var ss = parseTime(s.schedStart), se = parseTime(s.schedEnd);
  if (se <= ss) se += 1440;
  // 지각·조퇴는 소정 근무 시간대 안에서 시작한 근무만 판정한다(야간조 등은 판정 안 함).
  if (a < se) {
    out.lateMin = Math.max(0, a - (ss + Math.round(s.graceMin)));
    out.earlyMin = Math.max(0, (se - Math.round(s.graceMin)) - b);
  }
  return out;
}

// 합이 정확히 total이 되도록 가장 큰 나머지 순서로 나눔(정수)
function allocate(amounts, total) {
  var sum = amounts.reduce(function (a, b) { return a + b; }, 0);
  if (sum <= 0 || total <= 0) return amounts.map(function () { return 0; });
  var raw = amounts.map(function (a) { return a * total / sum; });
  var base = raw.map(Math.floor);
  var left = total - base.reduce(function (a, b) { return a + b; }, 0);
  var order = raw.map(function (r, i) { return { i: i, f: r - Math.floor(r) }; })
    .sort(function (x, y) { return y.f - x.f || x.i - y.i; });
  for (var k = 0; k < left; k++) base[order[k].i]++;
  return base;
}

function pad2(n) { return (n < 10 ? '0' : '') + n; }
function fmtHM(min) { min = Math.round(min); return Math.floor(min / 60) + '시간 ' + pad2(min % 60) + '분'; }
function fmtClock(min) { var m = ((min % 1440) + 1440) % 1440; return pad2(Math.floor(m / 60)) + ':' + pad2(m % 60); }
function won(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; }

// 전체 집계
function summarize(text, settingsIn, wagesText) {
  var s = normalize(settingsIn);
  var pr = parseRecords(text), wg = parseWages(wagesText);
  var errors = pr.errors.concat(wg.errors), warnings = [];
  if (s.month && !/^\d{4}-\d{2}$/.test(s.month)) { errors.push('집계 월은 2026-11 처럼 써 주세요 (' + s.month + ')'); s.month = ''; }
  var recs = pr.records.filter(function (r) { return !s.month || r.date.indexOf(s.month) === 0; });
  var days = [], emps = [], byName = {}, seen = {};
  recs.forEach(function (r) {
    var c = calcDay(r, s);
    var day = { line: r.line, name: r.name, date: r.date, inMin: r.inMin, outMin: r.outMin };
    Object.keys(c).forEach(function (k) { day[k] = c[k]; });
    days.push(day);
    var key = r.name + '|' + r.date;
    seen[key] = (seen[key] || 0) + 1;
    if (seen[key] === 2) warnings.push({ type: 'dup', name: r.name, date: r.date, message: r.name + ' ' + r.date + ' 같은 날 기록이 2건 이상입니다. 모두 더했으니 확인하세요.' });
    if (c.missing === 'in') warnings.push({ type: 'missing-in', name: r.name, date: r.date, message: r.name + ' ' + r.date + ' 퇴근만 있고 출근 기록이 없습니다. 시간에 넣지 않았습니다.' });
    else if (c.missing === 'out') warnings.push({ type: 'missing-out', name: r.name, date: r.date, message: r.name + ' ' + r.date + ' 출근만 있고 퇴근 기록이 없습니다. 시간에 넣지 않았습니다.' });
    else if (c.missing === 'both') warnings.push({ type: 'missing-both', name: r.name, date: r.date, message: r.name + ' ' + r.date + ' 출근·퇴근이 모두 비어 있습니다.' });
    else if (c.grossMin > 16 * 60) warnings.push({ type: 'long', name: r.name, date: r.date, message: r.name + ' ' + r.date + ' 하루 ' + fmtHM(c.grossMin) + ' 로 매우 깁니다. 시각을 확인하세요.' });
    var e = byName[r.name];
    if (!e) {
      e = byName[r.name] = { name: r.name, wage: wg.map[r.name] !== undefined ? wg.map[r.name] : s.defaultWage, days: 0, records: 0,
        grossMin: 0, breakMin: 0, workMin: 0, otMin: 0, nightMin: 0, lateCount: 0, lateMin: 0, earlyCount: 0, earlyMin: 0, missingCount: 0, payRaw: 0, pay: 0 };
      emps.push(e);
    }
    e.records++;
    if (c.missing) { e.missingCount++; return; }
    e.days++;
    e.grossMin += c.grossMin; e.breakMin += c.breakMin; e.workMin += c.workMin; e.otMin += c.otMin; e.nightMin += c.nightMin;
    if (c.lateMin > 0) { e.lateCount++; e.lateMin += c.lateMin; }
    if (c.earlyMin > 0) { e.earlyCount++; e.earlyMin += c.earlyMin; }
  });
  Object.keys(wg.map).forEach(function (n) { if (!byName[n] && recs.length) warnings.push({ type: 'wage-unused', name: n, date: '', message: '시급 목록의 ' + n + ' 은(는) 기록에 없습니다.' }); });
  // 급여 참고: 시급 × (근무분 + 연장분×가산 + 야간분×가산) / 60. 직원별 반올림 합이 아니라 전체를 한 번 반올림한 뒤 나눠서 합 보존.
  emps.forEach(function (e) {
    e.payRaw = e.wage * (e.workMin + e.otMin * s.otPremium + e.nightMin * s.nightPremium) / 60;
  });
  var rawSum = emps.reduce(function (a, e) { return a + e.payRaw; }, 0);
  var total = Math.round(rawSum);
  var parts = allocate(emps.map(function (e) { return e.payRaw; }), total);
  emps.forEach(function (e, i) { e.pay = parts[i]; });
  var totals = { days: 0, workMin: 0, otMin: 0, nightMin: 0, lateCount: 0, earlyCount: 0, missingCount: 0, pay: total };
  emps.forEach(function (e) {
    totals.days += e.days; totals.workMin += e.workMin; totals.otMin += e.otMin; totals.nightMin += e.nightMin;
    totals.lateCount += e.lateCount; totals.earlyCount += e.earlyCount; totals.missingCount += e.missingCount;
  });
  return { settings: s, days: days, employees: emps, totals: totals, warnings: warnings, errors: errors };
}

var SAMPLE_TEXT = '# 이름 날짜 출근 퇴근 (모르는 시각은 -)\n' +
  '홍길동 2026-11-02 09:00 20:00\n' +
  '홍길동 2026-11-03 09:12 18:00\n' +
  '홍길동 2026-11-04 09:00 -\n' +
  '김영희 2026-11-02 22:00 06:00\n' +
  '김영희 2026-11-03 21:30 07:30\n' +
  '김영희 2026-11-04 - 06:00\n' +
  '박민수 2026-11-02 09:00 17:30\n' +
  '박민수 2026-11-03 09:00 18:00\n';
var SAMPLE_WAGES = '홍길동=10500\n김영희=10320\n';

var api = { DEFAULTS: DEFAULTS, normalize: normalize, parseTime: parseTime, parseDate: parseDate, parseRecords: parseRecords,
  parseWages: parseWages, nightOverlap: nightOverlap, calcDay: calcDay, allocate: allocate, summarize: summarize,
  fmtHM: fmtHM, fmtClock: fmtClock, won: won, SAMPLE_TEXT: SAMPLE_TEXT, SAMPLE_WAGES: SAMPLE_WAGES };
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
