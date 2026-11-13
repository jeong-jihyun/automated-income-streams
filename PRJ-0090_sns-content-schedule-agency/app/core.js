// SNS 콘텐츠 일정 관리 대행 - 핵심 계산 (외부 연결 없음)
(function (root) {
  'use strict';
  var WD = ['월', '화', '수', '목', '금', '토', '일'];

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function isValidDate(y, m, d) {
    if (!(y >= 1900 && y <= 2200 && m >= 1 && m <= 12 && d >= 1)) return false;
    var dt = new Date(Date.UTC(y, m - 1, d));
    return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d;
  }
  function daysInMonth(y, m) { return new Date(Date.UTC(y, m, 0)).getUTCDate(); }
  // 월요일=0 ... 일요일=6
  function weekdayIdx(y, m, d) { return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7; }
  function dateKey(y, m, d) { return y + '-' + pad(m) + '-' + pad(d); }

  // 줄마다 "날짜, 채널, 제목" (쉼표 또는 탭). 날짜는 2026-11-05 또는 2026.11.5 형식.
  function parsePlan(text) {
    var items = [], errors = [];
    String(text == null ? '' : text).split(/\r?\n/).forEach(function (raw, i) {
      var line = raw.trim();
      if (!line || line.charAt(0) === '#') return;
      var parts = line.split(/\t|,/).map(function (s) { return s.trim(); });
      var title = parts.slice(2).join(', ');
      var mm = /^(\d{4})[-./](\d{1,2})[-./](\d{1,2})$/.exec(parts[0] || '');
      if (!mm) { errors.push({ line: i + 1, text: line, reason: '날짜 형식이 틀렸어요 (예: 2026-11-05)' }); return; }
      var y = +mm[1], m = +mm[2], d = +mm[3];
      if (!isValidDate(y, m, d)) { errors.push({ line: i + 1, text: line, reason: '없는 날짜예요' }); return; }
      if (!parts[1]) { errors.push({ line: i + 1, text: line, reason: '채널이 비어 있어요' }); return; }
      items.push({ y: y, m: m, d: d, date: dateKey(y, m, d), channel: parts[1], title: title, line: i + 1 });
    });
    return { items: items, errors: errors };
  }

  // 월 달력 칸: 주(월~일) 배열, 각 칸은 날짜 숫자 또는 null
  function buildCalendar(year, month, items) {
    var first = weekdayIdx(year, month, 1), n = daysInMonth(year, month);
    var cells = [];
    for (var i = 0; i < first; i++) cells.push(null);
    for (var d = 1; d <= n; d++) cells.push(d);
    while (cells.length % 7) cells.push(null);
    var byDay = {};
    (items || []).forEach(function (it) {
      if (it.y === year && it.m === month) (byDay[it.d] = byDay[it.d] || []).push(it);
    });
    var weeks = [];
    for (var k = 0; k < cells.length; k += 7) {
      weeks.push(cells.slice(k, k + 7).map(function (d2) {
        return d2 == null ? null : { day: d2, posts: byDay[d2] || [] };
      }));
    }
    return weeks;
  }

  // 점검: 중복, 빈 날, 주별 게시 수, 요일 쏠림
  function analyze(items, opts) {
    opts = opts || {};
    var year = opts.year, month = opts.month;
    var minPerWeek = opts.minPerWeek == null ? 3 : opts.minPerWeek;
    var skewPct = opts.skewPct == null ? 40 : opts.skewPct;
    var skipWeekend = !!opts.skipWeekendEmpty;
    var inMonth = items.filter(function (it) { return it.y === year && it.m === month; });
    var outside = items.length - inMonth.length;

    // 같은 날 같은 채널 중복
    var seen = {}, duplicates = [];
    inMonth.forEach(function (it) {
      var k = it.date + '|' + it.channel.toLowerCase();
      (seen[k] = seen[k] || []).push(it);
    });
    Object.keys(seen).forEach(function (k) {
      if (seen[k].length > 1) duplicates.push({ date: seen[k][0].date, channel: seen[k][0].channel, count: seen[k].length, titles: seen[k].map(function (x) { return x.title; }) });
    });
    duplicates.sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });

    // 빈 날
    var hasPost = {};
    inMonth.forEach(function (it) { hasPost[it.d] = true; });
    var emptyDays = [], n = daysInMonth(year, month);
    for (var d = 1; d <= n; d++) {
      if (hasPost[d]) continue;
      if (skipWeekend && weekdayIdx(year, month, d) >= 5) continue;
      emptyDays.push(d);
    }

    // 주별(월~일) 게시 수
    var weeks = buildCalendar(year, month, inMonth), weekCounts = [];
    weeks.forEach(function (w, i) {
      var cnt = 0, days = 0;
      w.forEach(function (c) { if (c) { cnt += c.posts.length; days++; } });
      weekCounts.push({ week: i + 1, count: cnt, daysInWeek: days, low: days === 7 && cnt < minPerWeek, partial: days < 7 });
    });

    // 요일 쏠림
    var wdCounts = [0, 0, 0, 0, 0, 0, 0];
    inMonth.forEach(function (it) { wdCounts[weekdayIdx(it.y, it.m, it.d)]++; });
    var total = inMonth.length, maxC = Math.max.apply(null, wdCounts);
    var maxIdx = wdCounts.indexOf(maxC);
    var share = total ? Math.round(maxC * 1000 / total) / 10 : 0;
    var skew = { counts: wdCounts, topWeekday: total ? WD[maxIdx] : null, topShare: share, skewed: total >= 5 && share > skewPct };

    var channels = {};
    inMonth.forEach(function (it) { channels[it.channel] = (channels[it.channel] || 0) + 1; });

    var warnings = [];
    if (duplicates.length) warnings.push('같은 날 같은 채널 중복 ' + duplicates.length + '건');
    if (emptyDays.length) warnings.push('게시 없는 날 ' + emptyDays.length + '일');
    var lows = weekCounts.filter(function (w) { return w.low; });
    if (lows.length) warnings.push('주당 ' + minPerWeek + '건 미만인 주(7일 다 이 달인 주만) ' + lows.length + '개');
    if (skew.skewed) warnings.push(skew.topWeekday + '요일에 ' + share + '% 쏠림');
    if (outside) warnings.push('선택한 달 밖의 일정 ' + outside + '건은 계산에서 뺐어요');

    return { total: total, outside: outside, duplicates: duplicates, emptyDays: emptyDays, weekCounts: weekCounts, skew: skew, channels: channels, warnings: warnings, ok: warnings.length === 0 };
  }

  // 합이 total이 되도록 weights 비율로 정수 나눔 (가장 큰 나머지 순으로 1원씩)
  function allocate(total, weights) {
    var sum = weights.reduce(function (a, b) { return a + b; }, 0);
    if (!weights.length) return [];
    if (sum <= 0) { // 균등 분배
      var b = Math.floor(total / weights.length), r = total - b * weights.length;
      return weights.map(function (_, i) { return b + (i < r ? 1 : 0); });
    }
    var base = weights.map(function (w) { return Math.floor(total * w / sum); });
    var rem = total - base.reduce(function (a, b2) { return a + b2; }, 0);
    var order = weights.map(function (w, i) { return { i: i, f: (total * w) % sum }; })
      .sort(function (a, b3) { return b3.f - a.f || a.i - b3.i; });
    for (var k = 0; k < rem; k++) base[order[k].i]++;
    return base;
  }

  // 월 견적: 공급가 = 단가 x 게시 수, 부가세 = 공급가 x 비율(반올림), 합계 = 공급가 + 부가세
  // 채널별 부가세는 합계 부가세에 맞춰 나머지 처리
  function quote(channels, unitPrice, vatPct) {
    unitPrice = Math.max(0, Math.round(Number(unitPrice) || 0));
    vatPct = vatPct == null ? 10 : Number(vatPct);
    var names = Object.keys(channels).sort();
    var counts = names.map(function (n) { return channels[n]; });
    var posts = counts.reduce(function (a, b) { return a + b; }, 0);
    var supply = unitPrice * posts;
    var vat = Math.round(supply * vatPct / 100);
    var vats = allocate(vat, counts.map(function (c) { return c * unitPrice; }));
    var rows = names.map(function (n, i) {
      var s = counts[i] * unitPrice;
      return { channel: n, posts: counts[i], supply: s, vat: vats[i], total: s + vats[i] };
    });
    return { unitPrice: unitPrice, vatPct: vatPct, posts: posts, supply: supply, vat: vat, total: supply + vat, rows: rows };
  }

  function won(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; }

  var api = { WD: WD, parsePlan: parsePlan, buildCalendar: buildCalendar, analyze: analyze, allocate: allocate, quote: quote, won: won, isValidDate: isValidDate, daysInMonth: daysInMonth, weekdayIdx: weekdayIdx };
  if (typeof module !== 'undefined') module.exports = api;
  else root.SnsCore = api;
})(typeof window !== 'undefined' ? window : this);
