'use strict';
// 핵심 점검·계산. 화면(index.html)은 이 파일을 불러 쓴다. 번역은 하지 않는다(외부 AI 호출 없음).

// ---------- 문단 나누기 ----------
// 구분: 줄에 '---'(대시 3개 이상)만 있으면 그 줄이 구분선(빈 문단도 셀 수 있음). 없으면 빈 줄로 나눈다.
function hasDashSeparator(text) { return /^[ \t]*-{3,}[ \t]*$/m.test(String(text || '').replace(/\r\n?/g, '\n')); }

function splitParagraphs(text, mode) {
  var s = String(text || '').replace(/^﻿/, '').replace(/\r\n?/g, '\n').trim();
  if (!s) return [];
  var parts = mode === 'dash' ? s.split(/^[ \t]*-{3,}[ \t]*$/m) : s.split(/\n[ \t]*\n/);
  return parts.map(function (p) { return p.trim(); });
}

var PLACEHOLDER = /^(?:[-–—.…?]+|tbd|todo|n\/a|번역 ?(?:필요|없음)|미번역)$/i;
function isEmptyPara(t) { var s = String(t).trim(); return s === '' || PLACEHOLDER.test(s); }
function countChars(text) { return String(text).replace(/\s/g, '').length; }

// ---------- 용어집 ----------
// 한 줄에 '원어=번역어'. 번역어를 '|'로 여러 개 적으면 그중 하나만 있어도 통과. '#'로 시작하면 주석.
function parseGlossary(text) {
  var entries = [], errors = [];
  String(text || '').replace(/\r\n?/g, '\n').split('\n').forEach(function (raw, i) {
    var line = raw.trim();
    if (!line || line.charAt(0) === '#') return;
    var k = line.indexOf('=');
    if (k < 0) { errors.push((i + 1) + '째 줄: "원어=번역어" 모양이 아닙니다.'); return; }
    var src = line.slice(0, k).trim();
    var alts = line.slice(k + 1).split('|').map(function (a) { return a.trim(); }).filter(Boolean);
    if (!src || !alts.length) { errors.push((i + 1) + '째 줄: = 양쪽에 글자가 있어야 합니다.'); return; }
    entries.push({ src: src, alts: alts });
  });
  return { entries: entries, errors: errors };
}

function isAlnum(ch) { return /[A-Za-z0-9]/.test(ch || ''); }
// 영문·숫자로 시작/끝나는 용어는 단어 경계를 지켜 찾는다(plan이 planning에 걸리지 않게).
function containsTerm(text, term) {
  var t = String(text).toLowerCase(), q = String(term).toLowerCase();
  if (!q) return false;
  var from = 0, at;
  while ((at = t.indexOf(q, from)) >= 0) {
    var before = at > 0 ? t.charAt(at - 1) : '', after = t.charAt(at + q.length);
    var okB = !(isAlnum(q.charAt(0)) && isAlnum(before));
    var okA = !(isAlnum(q.charAt(q.length - 1)) && isAlnum(after));
    if (okB && okA) return true;
    from = at + 1;
  }
  return false;
}

// ---------- 날짜·주소·숫자·고유명사 뽑기 ----------
var MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
var MON_RE = '(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\\.?';

function mkDate(y, m, d) { return { y: y ? +y : null, m: +m, d: +d }; }

// 날짜를 찾아 [{y,m,d,raw}]와 날짜를 지운 글을 돌려준다.
function extractDates(text) {
  var found = [], s = String(text);
  function grab(re, f) {
    s = s.replace(re, function () {
      var a = Array.prototype.slice.call(arguments);
      var dt = f(a);
      if (!dt || dt.m < 1 || dt.m > 12 || dt.d < 1 || dt.d > 31) return a[0];
      dt.raw = a[0]; found.push(dt); return ' ';
    });
  }
  grab(/(\d{4})\s*[-./]\s*(\d{1,2})\s*[-./]\s*(\d{1,2})(?!\d)/g, function (a) { return mkDate(a[1], a[2], a[3]); });
  grab(/(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일/g, function (a) { return mkDate(a[1], a[2], a[3]); });
  grab(new RegExp('\\b' + MON_RE + '\\s+(\\d{1,2})(?:st|nd|rd|th)?(?:\\s*,?\\s*(\\d{4}))?(?!\\d)', 'gi'),
    function (a) { return mkDate(a[3], MONTHS[a[1].slice(0, 3).toLowerCase()], a[2]); });
  grab(new RegExp('\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+' + MON_RE + '(?:\\s*,?\\s*(\\d{4}))?(?!\\d)', 'gi'),
    function (a) { return mkDate(a[3], MONTHS[a[2].slice(0, 3).toLowerCase()], a[1]); });
  grab(/(\d{1,2})\s*월\s*(\d{1,2})\s*일/g, function (a) { return mkDate(null, a[1], a[2]); });
  return { dates: found, rest: s };
}

function dateLabel(d) { return (d.y ? d.y + '-' : '') + d.m + '-' + d.d; }

// 연도가 한쪽에 없으면 월·일만 비교한다.
function sameDate(a, b) { return a.m === b.m && a.d === b.d && (a.y === null || b.y === null || a.y === b.y); }

// 외부 주소 모양(코드에 프로토콜 글자를 그대로 쓰지 않으려고 조각을 이어 붙인다)
var URL_RE = new RegExp('(?:' + 'ht' + 'tps?:\\/\\/|www\\.)[^\\s<>"\'\\)\\]]+', 'gi');

function extractUrls(text) {
  var urls = [], rest = String(text).replace(URL_RE, function (m) {
    urls.push(m.replace(/[.,;:!?。、]+$/, '')); return ' ';
  });
  return { urls: urls, rest: rest };
}
function normUrl(u) { return u.toLowerCase().replace(/^[a-z]+:\/\//, '').replace(/^www\./, '').replace(/\/+$/, ''); }

function trimNum(n) { var s = String(n); return s.indexOf('.') >= 0 ? s.replace(/0+$/, '').replace(/\.$/, '') : s; }

function extractNumbers(text) {
  var s = String(text);
  s = s.replace(/(\d+(?:,\d{3})*(?:\.\d+)?)\s*(억|만|천)/g, function (m, n, u) {
    return ' ' + trimNum(Math.round(parseFloat(n.replace(/,/g, '')) * ({ '억': 1e8, '만': 1e4, '천': 1e3 })[u] * 1e6) / 1e6) + ' ';
  });
  s = s.replace(/(\d+(?:\.\d+)?)\s*(million|billion|thousand)\b/gi, function (m, n, u) {
    return ' ' + trimNum(Math.round(parseFloat(n) * ({ million: 1e6, billion: 1e9, thousand: 1e3 })[u.toLowerCase()] * 1e6) / 1e6) + ' ';
  });
  var out = [];
  (s.match(/\d+(?:,\d{3})*(?:\.\d+)?/g) || []).forEach(function (m) { out.push(trimNum(m.replace(/,/g, ''))); });
  return out;
}

var START_WORDS = { the: 1, a: 1, an: 1, our: 1, your: 1, my: 1, we: 1, you: 1, i: 1, it: 1, this: 1, that: 1, these: 1, those: 1,
  please: 1, if: 1, in: 1, on: 1, at: 1, for: 1, to: 1, and: 1, but: 1, or: 1, as: 1, with: 1, from: 1, by: 1, of: 1, he: 1, she: 1, they: 1,
  is: 1, are: 1, thank: 1, thanks: 1, hello: 1, hi: 1, welcome: 1, see: 1, visit: 1, contact: 1, click: 1, note: 1, all: 1, each: 1, when: 1, after: 1, before: 1,
  monday: 1, tuesday: 1, wednesday: 1, thursday: 1, friday: 1, saturday: 1, sunday: 1 };

// 영문 고유명사 후보: 문장 첫머리가 아닌 대문자 단어(연속은 하나로), 두 글자 이상 대문자 약어.
function extractProperNouns(text) {
  var s = String(text), re = /[A-Za-z][A-Za-z0-9'’&-]*/g, m, toks = [];
  while ((m = re.exec(s))) toks.push({ w: m[0], pos: m.index, end: m.index + m[0].length });
  function atStart(pos) { return /(?:^|[.!?]["'”’)]*\s+|\n\s*)$/.test(s.slice(0, pos)); }
  var out = [], seen = {}, i = 0;
  while (i < toks.length) {
    var t = toks[i];
    if (!/^[A-Z]/.test(t.w)) { i++; continue; }
    var j = i, parts = [t.w];
    while (j + 1 < toks.length && /^[A-Z]/.test(toks[j + 1].w) && /^ $/.test(s.slice(toks[j].end, toks[j + 1].pos))) { j++; parts.push(toks[j].w); }
    var start = atStart(t.pos);
    if (start && START_WORDS[parts[0].toLowerCase()]) parts.shift();
    else if (start && parts.length === 1 && !/^[A-Z]{2,}/.test(parts[0])) parts = [];
    while (parts.length && START_WORDS[parts[0].toLowerCase()] && !/^[A-Z]{2,}/.test(parts[0]) && parts.length > 1) parts.shift();
    if (parts.length) {
      var name = parts.join(' ');
      if (!/^[A-Z]{2,}/.test(name) && name.length < 2) name = '';
      if (name && !seen[name.toLowerCase()]) { seen[name.toLowerCase()] = 1; out.push(name); }
    }
    i = j + 1;
  }
  return out;
}

// ---------- 점검 ----------
var SEVERITY = { count: '오류', empty: '오류', number: '오류', date: '오류', url: '오류', glossary: '오류', proper: '확인', ratio: '확인' };

function countMap(arr) { var m = {}; arr.forEach(function (x) { m[x] = (m[x] || 0) + 1; }); return m; }

function checkPair(src, tgt, glossary, opts, n, push) {
  var emptyS = isEmptyPara(src), emptyT = isEmptyPara(tgt);
  if (emptyT && !emptyS) { push(n, 'empty', n + '번 문단: 번역문이 비어 있습니다.'); return; }
  if (emptyS && !emptyT) { push(n, 'empty', n + '번 문단: 원문이 비어 있는데 번역문에는 글이 있습니다.'); return; }
  if (emptyS && emptyT) { push(n, 'empty', n + '번 문단: 원문과 번역문이 모두 비어 있습니다.'); return; }

  var ds = extractDates(src), dt = extractDates(tgt);
  var pool = dt.dates.slice();
  ds.dates.forEach(function (d) {
    var k = -1;
    for (var i = 0; i < pool.length; i++) if (sameDate(d, pool[i])) { k = i; break; }
    if (k >= 0) pool.splice(k, 1);
    else push(n, 'date', n + '번 문단: 원문 날짜 "' + d.raw + '"(' + dateLabel(d) + ')이 번역문에 없습니다.');
  });
  pool.forEach(function (d) { push(n, 'date', n + '번 문단: 번역문에만 있는 날짜 "' + d.raw + '"(' + dateLabel(d) + ')'); });

  var us = extractUrls(ds.rest), ut = extractUrls(dt.rest);
  var tmap = countMap(ut.urls.map(normUrl));
  us.urls.forEach(function (u) {
    var k = normUrl(u);
    if (tmap[k] > 0) tmap[k]--; else push(n, 'url', n + '번 문단: 원문 주소 "' + u + '"가 번역문에 그대로 없습니다.');
  });
  var smap = countMap(us.urls.map(normUrl));
  ut.urls.forEach(function (u) {
    var k = normUrl(u);
    if (smap[k] > 0) smap[k]--; else push(n, 'url', n + '번 문단: 번역문에만 있는 주소 "' + u + '"');
  });

  var ns = countMap(extractNumbers(us.rest)), nt = countMap(extractNumbers(ut.rest));
  Object.keys(ns).forEach(function (k) {
    if ((nt[k] || 0) < ns[k]) push(n, 'number', n + '번 문단: 숫자 ' + k + ' 이(가) 원문에 ' + ns[k] + '번, 번역문에 ' + (nt[k] || 0) + '번 나옵니다.');
  });
  Object.keys(nt).forEach(function (k) {
    if (!ns[k]) push(n, 'number', n + '번 문단: 번역문에만 있는 숫자 ' + k);
  });

  var covered = {};
  glossary.entries.forEach(function (g) {
    if (!containsTerm(src, g.src)) return;
    covered[g.src.toLowerCase()] = 1;
    var ok = g.alts.some(function (a) { return containsTerm(tgt, a); });
    if (!ok) push(n, 'glossary', n + '번 문단: 용어집 위반 "' + g.src + '" → "' + g.alts.join('" 또는 "') + '" 이(가) 번역문에 없습니다.');
  });

  extractProperNouns(us.rest).forEach(function (p) {
    if (covered[p.toLowerCase()]) return;
    if (containsTerm(ut.rest, p) || containsTerm(tgt, p)) return;
    push(n, 'proper', n + '번 문단: 고유명사 후보 "' + p + '"가 번역문에 그대로 없습니다. 음역했다면 용어집에 넣어 두세요.');
  });

  var minLen = opts.minLen, cs = countChars(src), ct = countChars(tgt);
  if (cs >= minLen) {
    var ratio = ct / cs;
    if (ratio < opts.minRatio) push(n, 'ratio', n + '번 문단: 번역문이 너무 짧습니다 (원문의 ' + Math.round(ratio * 100) + '%, 기준 ' + Math.round(opts.minRatio * 100) + '% 이상). 빠진 내용이 없는지 확인하세요.');
    else if (ratio > opts.maxRatio) push(n, 'ratio', n + '번 문단: 번역문이 너무 깁니다 (원문의 ' + Math.round(ratio * 100) + '%, 기준 ' + Math.round(opts.maxRatio * 100) + '% 이하). 덧붙은 내용이 없는지 확인하세요.');
  }
}

// 원문·번역문 글(문단 구분) + 용어집 글 -> 점검 결과
function checkTranslation(srcText, tgtText, glossaryText, options) {
  options = options || {};
  var opts = {
    minRatio: options.minRatio > 0 ? +options.minRatio : 0.3,
    maxRatio: options.maxRatio > 0 ? +options.maxRatio : 3,
    minLen: options.minLen >= 0 ? +options.minLen : 10
  };
  var mode = (hasDashSeparator(srcText) || hasDashSeparator(tgtText)) ? 'dash' : 'blank';
  var sp = splitParagraphs(srcText, mode), tp = splitParagraphs(tgtText, mode);
  var glossary = parseGlossary(glossaryText);
  var issues = [];
  function push(para, type, message) { issues.push({ para: para, type: type, severity: SEVERITY[type], message: message }); }

  if (!sp.length && !tp.length) push(0, 'count', '원문과 번역문이 모두 비어 있습니다.');
  else if (sp.length !== tp.length) push(0, 'count', '문단 수가 다릅니다: 원문 ' + sp.length + '개, 번역문 ' + tp.length + '개. 앞에서부터 ' + Math.min(sp.length, tp.length) + '개만 짝지어 비교했습니다.');
  var pairs = Math.min(sp.length, tp.length);
  for (var i = 0; i < pairs; i++) checkPair(sp[i], tp[i], glossary, opts, i + 1, push);

  var errors = issues.filter(function (x) { return x.severity === '오류'; }).length;
  return {
    mode: mode, srcCount: sp.length, tgtCount: tp.length, paired: pairs,
    issues: issues, errors: errors, warnings: issues.length - errors,
    glossaryCount: glossary.entries.length, glossaryErrors: glossary.errors
  };
}

// ---------- 단어 수·견적 ----------
// 띄어쓰기로 나뉜 덩어리를 한 단어로 세고, 한자·가나는 글자 하나를 한 단어로 센다.
function countWords(text) {
  var s = String(text || ''), cjk = 0;
  s = s.replace(/[぀-ヿ㐀-鿿]/g, function () { cjk++; return ' '; });
  var latin = s.split(/\s+/).filter(function (t) { return /[A-Za-z0-9가-힣]/.test(t); }).length;
  return latin + cjk;
}

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

function nonNeg(v) { var n = Number(v); return isFinite(n) && n > 0 ? n : 0; }

// 견적: 단어 수×번역 단가 + 검수·재검수(단어 수×단가) + 서식(정액). 부가세 10%.
function quote(input) {
  var words = Math.floor(nonNeg(input.words));
  var parts = [
    { name: '번역(AI 초벌)', supply: Math.round(words * nonNeg(input.ratePerWord)) },
    { name: '검수', supply: Math.round(words * nonNeg(input.reviewPerWord)) },
    { name: '재검수', supply: Math.round(words * nonNeg(input.reReviewPerWord)) },
    { name: '서식 정리', supply: Math.round(nonNeg(input.formatFee)) }
  ];
  var supply = parts.reduce(function (a, p) { return a + p.supply; }, 0);
  var vat = Math.round(supply * 0.1);
  var vp = allocate(parts.map(function (p) { return p.supply; }), vat);
  return {
    words: words,
    items: parts.map(function (p, i) { return { name: p.name, supply: p.supply, vat: vp[i], total: p.supply + vp[i] }; }),
    supply: supply, vat: vat, total: supply + vat
  };
}

function won(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; }

var SAMPLE_SRC = 'Welcome to Acme Cloud. Our new Smart Dashboard launches on March 5, 2026 for all customers.\n---\n' +
  'The Basic plan costs $29 per month and includes 5 users. Visit www.acme.example/pricing for details.\n---\n' +
  'Our CEO, Maria Lopez, will present at the Seoul office.\n---\n' +
  'Thank you.\n---\n' +
  'Please read the attached guide carefully before you begin the setup process, because skipping any of the steps may cause errors later.\n---\n' +
  'See you soon!';
var SAMPLE_TGT = 'Acme Cloud에 오신 것을 환영합니다. 새로운 스마트 대시보드는 모든 고객에게 2026년 3월 15일에 출시됩니다.\n---\n' +
  '베이직 요금제는 월 $39이며 사용자 5명이 포함됩니다. 자세한 내용은 www.acme.example/price 에서 확인하세요.\n---\n' +
  '저희 대표 마리아 로페즈가 서울 사무실에서 발표합니다.\n---\n' +
  '\n---\n' +
  '설정을 시작하기 전에 첨부된 안내서를 읽으세요.\n---\n' +
  '곧 만나요!';
var SAMPLE_GLOSSARY = '# 원어=번역어 (여러 개면 | 로 구분)\nSmart Dashboard=스마트 대시보드\nBasic=베이직\nMaria Lopez=마리아 로페스\nSeoul=서울\nplan=요금제';

var api = {
  hasDashSeparator: hasDashSeparator, splitParagraphs: splitParagraphs, isEmptyPara: isEmptyPara, countChars: countChars,
  parseGlossary: parseGlossary, containsTerm: containsTerm,
  extractDates: extractDates, extractUrls: extractUrls, extractNumbers: extractNumbers, extractProperNouns: extractProperNouns,
  checkTranslation: checkTranslation, countWords: countWords, allocate: allocate, quote: quote, won: won,
  SAMPLE_SRC: SAMPLE_SRC, SAMPLE_TGT: SAMPLE_TGT, SAMPLE_GLOSSARY: SAMPLE_GLOSSARY
};
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
