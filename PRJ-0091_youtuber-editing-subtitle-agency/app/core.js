'use strict';
// 핵심 계산·판정. 화면(index.html)은 이 파일을 불러 쓴다.

function parseTime(s) {
  var m = /^\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*$/.exec(String(s));
  if (!m) return null;
  var mi = +m[2], se = +m[3];
  if (mi > 59 || se > 59) return null;
  var ms = +(m[4] + '00').slice(0, 3);
  return ((+m[1] * 60 + mi) * 60 + se) * 1000 + ms;
}

function formatTime(ms) {
  ms = Math.max(0, Math.round(ms));
  var h = Math.floor(ms / 3600000); ms -= h * 3600000;
  var m = Math.floor(ms / 60000); ms -= m * 60000;
  var s = Math.floor(ms / 1000); ms -= s * 1000;
  var p = function (n, w) { return String(n).padStart(w, '0'); };
  return p(h, 2) + ':' + p(m, 2) + ':' + p(s, 2) + ',' + p(ms, 3);
}

// SRT 글 -> { cues, errors }
function parseSrt(text) {
  var cues = [], errors = [];
  var src = String(text || '').replace(/^﻿/, '').replace(/\r\n?/g, '\n').trim();
  if (!src) return { cues: cues, errors: ['자막 글이 비어 있습니다.'] };
  var blocks = src.split(/\n\s*\n/);
  blocks.forEach(function (b, bi) {
    var lines = b.split('\n');
    var i = 0;
    var idx = cues.length + 1;
    if (/^\d+$/.test(lines[0].trim())) { idx = +lines[0].trim(); i = 1; }
    var tl = lines[i] || '';
    var m = /^(.+?)\s*-->\s*(.+)$/.exec(tl);
    if (!m) { errors.push((bi + 1) + '번째 덩어리: 시간 줄(00:00:01,000 --> 00:00:03,000)을 찾지 못했습니다.'); return; }
    var st = parseTime(m[1]), en = parseTime(m[2]);
    if (st === null || en === null) { errors.push((bi + 1) + '번째 덩어리: 시간 모양이 올바르지 않습니다.'); return; }
    cues.push({ index: idx, start: st, end: en, text: lines.slice(i + 1).join('\n').trim() });
  });
  return { cues: cues, errors: errors };
}

function buildSrt(cues) {
  return cues.map(function (c, i) {
    return (i + 1) + '\n' + formatTime(c.start) + ' --> ' + formatTime(c.end) + '\n' + c.text;
  }).join('\n\n') + (cues.length ? '\n' : '');
}

// 글자 수(줄바꿈·공백 제외)
function countChars(text) { return String(text).replace(/\s/g, '').length; }

// 점검: 겹침, 긴 줄, 초당 글자 수 초과, 길이 0 이하
function checkCues(cues, opts) {
  opts = opts || {};
  var maxLine = opts.maxLineChars > 0 ? opts.maxLineChars : 20;
  var maxCps = opts.maxCps > 0 ? opts.maxCps : 12;
  var issues = [];
  cues.forEach(function (c, i) {
    var n = i + 1;
    if (c.end <= c.start) issues.push({ cue: n, type: 'duration', message: n + '번: 끝 시간이 시작 시간보다 빠르거나 같습니다.' });
    var next = cues[i + 1];
    if (next && c.end > next.start) {
      issues.push({ cue: n, type: 'overlap', message: n + '번과 ' + (n + 1) + '번이 ' + (c.end - next.start) + 'ms 겹칩니다.' });
    }
    String(c.text).split('\n').forEach(function (ln, li) {
      var len = ln.replace(/\s/g, '').length;
      if (len > maxLine) issues.push({ cue: n, type: 'long', message: n + '번 ' + (li + 1) + '째 줄: ' + len + '자 (기준 ' + maxLine + '자 초과)' });
    });
    var dur = (c.end - c.start) / 1000;
    if (dur > 0) {
      var cps = countChars(c.text) / dur;
      if (cps > maxCps + 1e-9) issues.push({ cue: n, type: 'cps', message: n + '번: 초당 ' + cps.toFixed(1) + '자 (기준 ' + maxCps + '자 초과)' });
    }
  });
  return issues;
}

// 시간 이동(초, 음수 가능). 0보다 앞으로는 못 가서 0에 멈춘다.
function shiftCues(cues, seconds) {
  var d = Math.round(Number(seconds) * 1000);
  if (!isFinite(d)) d = 0;
  var clamped = 0;
  var out = cues.map(function (c) {
    var s = c.start + d, e = c.end + d;
    if (s < 0 || e < 0) clamped++;
    return { index: c.index, start: Math.max(0, s), end: Math.max(0, e), text: c.text };
  });
  return { cues: out, clamped: clamped };
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

// 견적: 영상 길이(분)×분당 단가 + 자막 수정 횟수×1회 단가. 부가세 10%.
function quote(input) {
  var minutes = Math.max(0, Number(input.minutes) || 0);
  var rate = Math.max(0, Math.round(Number(input.ratePerMin) || 0));
  var edits = Math.max(0, Math.floor(Number(input.edits) || 0));
  var editFee = Math.max(0, Math.round(Number(input.editFee) || 0));
  var editing = Math.round(minutes * rate);
  var revise = edits * editFee;
  var supply = editing + revise;
  var vat = Math.round(supply * 0.1);
  var total = supply + vat;
  var vatParts = allocate([editing, revise], vat);
  return {
    items: [
      { name: '편집·자막 작업', supply: editing, vat: vatParts[0], total: editing + vatParts[0] },
      { name: '자막 수정', supply: revise, vat: vatParts[1], total: revise + vatParts[1] }
    ],
    supply: supply, vat: vat, total: total
  };
}

function won(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; }

var SAMPLE_SRT = '1\n00:00:01,000 --> 00:00:03,500\n안녕하세요, 오늘은 편집 방법을 알려 드릴게요.\n\n' +
  '2\n00:00:03,000 --> 00:00:05,000\n먼저 영상을 불러옵니다.\n\n' +
  '3\n00:00:05,500 --> 00:00:07,000\n이 줄은 너무 길어서 한 화면에 읽기 어려운 자막 예시입니다 정말로요\n\n' +
  '4\n00:00:08,000 --> 00:00:10,000\n자막 시간을 맞춰 봅시다.\n';

var api = { parseTime: parseTime, formatTime: formatTime, parseSrt: parseSrt, buildSrt: buildSrt,
  countChars: countChars, checkCues: checkCues, shiftCues: shiftCues, allocate: allocate,
  quote: quote, won: won, SAMPLE_SRT: SAMPLE_SRT };
if (typeof module !== 'undefined') module.exports = api;
if (typeof window !== 'undefined') window.Core = api;
