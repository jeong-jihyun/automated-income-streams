/* 고객 문의 접수·분류 구축 - 핵심 계산 (순수 JS, 인터넷 불필요) */
(function (root) {
  'use strict';

  var OTHER_TEAM = '기타(담당 미정)';

  // 기본 규칙: 담당 칸 + 키워드. 앞에 있는 규칙이 점수가 같을 때 우선한다.
  var DEFAULT_RULES = [
    { team: '배송', keywords: ['배송', '택배', '송장', '도착', '운송장', '출고', '배달', '언제 와', '안 와', '안와', '지연'] },
    { team: '환불·교환', keywords: ['환불', '반품', '교환', '취소', '철회', '반송', '불량', '파손', '환급'] },
    { team: '결제', keywords: ['결제', '카드', '입금', '이중결제', '중복결제', '영수증', '승인', '무통장', '계좌', '청구'] },
    { team: '사용법', keywords: ['사용법', '어떻게', '방법', '설치', '로그인', '비밀번호', '설정', '사용', '안 돼', '안돼', '오류', '작동'] }
  ];

  // 긴급도 규칙
  var DEFAULT_URGENCY = {
    angry: ['화가', '화나', '짜증', '최악', '어이없', '황당', '열받', '불쾌', '실망', '답답', '항의', '사기', '신고', '소비자원', '고소', '다시는', '도대체', '쓰레기'],
    deadline: ['오늘까지', '오늘 안', '오늘중', '오늘 중', '내일까지', '당장', '지금 바로', '지금바로', '즉시', '긴급', '급해', '급합니다', '빨리', '시급', '바로 확인', 'asap'],
    repeat: ['몇 번째', '몇번째', '또 ', '여러 번', '여러번', '계속', '아직도', '벌써', '재문의', '답이 없'],
    weights: { angry: 2, deadline: 3, repeat: 1, exclaim: 1 },
    urgentAt: 5,
    cautionAt: 2
  };

  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  function normalize(s) {
    return String(s == null ? '' : s).toLowerCase().replace(/\s+/g, ' ').trim();
  }

  // 여러 줄 입력 -> 문의 목록. 빈 줄 무시, 앞의 번호/불릿 제거.
  function splitInquiries(text) {
    return String(text == null ? '' : text)
      .split(/\r?\n/)
      .map(function (l) { return l.replace(/^\s*(?:[-*•]|\d+[.)])\s+/, '').trim(); })
      .filter(function (l) { return l.length > 0; });
  }

  function findHits(normText, keywords) {
    var hits = [];
    for (var i = 0; i < keywords.length; i++) {
      var k = normalize(keywords[i]);
      if (k && normText.indexOf(k) !== -1 && hits.indexOf(keywords[i]) === -1) hits.push(keywords[i]);
    }
    return hits;
  }

  // 분류: 겹치지 않는 키워드가 가장 많이 맞는 칸. 동점이면 앞 규칙.
  function classify(text, rules) {
    var t = normalize(text);
    var best = null;
    (rules || []).forEach(function (r, idx) {
      var hits = findHits(t, r.keywords || []);
      if (hits.length > 0 && (!best || hits.length > best.hits.length)) {
        best = { team: r.team, hits: hits, order: idx };
      }
    });
    if (!best) return { team: OTHER_TEAM, hits: [], order: -1 };
    return best;
  }

  function countExclaim(text) {
    var m = String(text).match(/[!?！？]{2,}|!{2,}/g);
    return m ? m.length : 0;
  }

  // 긴급도 점수와 이유
  function urgency(text, cfg) {
    cfg = cfg || DEFAULT_URGENCY;
    var w = cfg.weights || DEFAULT_URGENCY.weights;
    var t = normalize(text);
    var angry = findHits(t, cfg.angry || []);
    var deadline = findHits(t, cfg.deadline || []);
    var repeat = findHits(t, cfg.repeat || []);
    var ex = countExclaim(text);
    var score = Math.min(angry.length, 3) * w.angry +
      Math.min(deadline.length, 2) * w.deadline +
      Math.min(repeat.length, 2) * w.repeat +
      Math.min(ex, 2) * w.exclaim;
    var reasons = [];
    if (angry.length) reasons.push('화난 표현: ' + angry.join(', '));
    if (deadline.length) reasons.push('기한 표현: ' + deadline.join(', '));
    if (repeat.length) reasons.push('반복 문의: ' + repeat.join(', '));
    if (ex) reasons.push('느낌표/물음표 연속');
    var urgentAt = cfg.urgentAt == null ? 5 : cfg.urgentAt;
    var cautionAt = cfg.cautionAt == null ? 2 : cfg.cautionAt;
    var level = score >= urgentAt ? '긴급' : (score >= cautionAt ? '주의' : '보통');
    return { score: score, level: level, reasons: reasons };
  }

  function levelRank(level) { return level === '긴급' ? 2 : (level === '주의' ? 1 : 0); }

  // 일괄 처리: 입력 전체 -> 항목들
  function processBatch(text, rules, urgencyCfg) {
    var lines = splitInquiries(text);
    return lines.map(function (line, i) {
      var c = classify(line, rules);
      var u = urgency(line, urgencyCfg);
      return {
        no: i + 1, text: line, team: c.team, matched: c.hits,
        score: u.score, level: u.level, reasons: u.reasons
      };
    });
  }

  // 담당 칸별 묶음. 칸 안은 긴급도 높은 순(동점은 입력 순). 칸 순서는 규칙 순서, 기타는 맨 뒤.
  function groupByTeam(items, rules) {
    var order = (rules || []).map(function (r) { return r.team; });
    var map = {};
    items.forEach(function (it) { (map[it.team] = map[it.team] || []).push(it); });
    var teams = Object.keys(map).sort(function (a, b) {
      var ia = order.indexOf(a), ib = order.indexOf(b);
      if (ia === -1) ia = 9999; if (ib === -1) ib = 9999;
      return ia - ib;
    });
    return teams.map(function (t) {
      var list = map[t].slice().sort(function (a, b) { return (b.score - a.score) || (a.no - b.no); });
      return {
        team: t, items: list,
        urgentCount: list.filter(function (x) { return x.level === '긴급'; }).length
      };
    });
  }

  function summarize(items) {
    var s = { total: items.length, urgent: 0, caution: 0, normal: 0, unassigned: 0 };
    items.forEach(function (it) {
      if (it.level === '긴급') s.urgent++; else if (it.level === '주의') s.caution++; else s.normal++;
      if (it.team === OTHER_TEAM) s.unassigned++;
    });
    return s;
  }

  // 규칙 편집용 글 형식: "담당칸: 키워드, 키워드" 한 줄에 한 칸
  function rulesToText(rules) {
    return rules.map(function (r) { return r.team + ': ' + r.keywords.join(', '); }).join('\n');
  }

  function parseRules(text) {
    var rules = [], errors = [], seen = {};
    String(text == null ? '' : text).split(/\r?\n/).forEach(function (line, i) {
      var l = line.trim();
      if (!l) return;
      var p = l.search(/[:：]/);
      if (p < 1) { errors.push((i + 1) + '번째 줄: "칸 이름: 키워드, 키워드" 모양이 아니에요'); return; }
      var team = l.slice(0, p).trim();
      var kws = l.slice(p + 1).split(/[,，]/).map(function (k) { return k.trim(); }).filter(Boolean);
      if (!team) { errors.push((i + 1) + '번째 줄: 칸 이름이 비었어요'); return; }
      if (kws.length === 0) { errors.push((i + 1) + '번째 줄: 키워드가 없어요'); return; }
      if (seen[team]) { errors.push((i + 1) + '번째 줄: 칸 이름 "' + team + '"이(가) 겹쳐요'); return; }
      seen[team] = true;
      rules.push({ team: team, keywords: kws });
    });
    return { rules: rules, errors: errors };
  }

  // 긴급도 단어 목록 편집용 (한 줄 한 종류)
  function urgencyToText(cfg) {
    return '화난 표현: ' + cfg.angry.join(', ') + '\n기한 표현: ' + cfg.deadline.join(', ') + '\n반복 표현: ' + cfg.repeat.join(', ');
  }

  function parseUrgency(text, base) {
    var cfg = clone(base || DEFAULT_URGENCY), errors = [];
    var keys = { '화난 표현': 'angry', '기한 표현': 'deadline', '반복 표현': 'repeat' };
    var found = {};
    String(text == null ? '' : text).split(/\r?\n/).forEach(function (line, i) {
      var l = line.trim();
      if (!l) return;
      var p = l.search(/[:：]/);
      var name = p > 0 ? l.slice(0, p).trim() : '';
      if (!keys[name]) { errors.push((i + 1) + '번째 줄: "화난 표현/기한 표현/반복 표현: 단어, 단어" 모양이어야 해요'); return; }
      cfg[keys[name]] = l.slice(p + 1).split(/[,，]/).map(function (k) { return k.trim(); }).filter(Boolean);
      found[name] = true;
    });
    return { cfg: cfg, errors: errors };
  }

  // 담당 칸별 결과를 복사용 글로 만든다 (전송 기능 없음, 화면에 보여 주기만)
  function toPlainText(groups) {
    var out = [];
    groups.forEach(function (g) {
      out.push('[' + g.team + '] ' + g.items.length + '건' + (g.urgentCount ? ' (긴급 ' + g.urgentCount + ')' : ''));
      g.items.forEach(function (it) { out.push('  - (' + it.level + ') ' + it.text); });
    });
    return out.join('\n');
  }

  var SAMPLE_TEXT = [
    '택배가 일주일째 안 와요. 언제 도착하나요?',
    '환불해 주세요. 불량품이 왔는데 너무 화가 납니다!!',
    '이중결제 된 것 같아서 너무 화가 나요. 오늘까지 확인 안 되면 신고할게요!!',
    '로그인 비밀번호를 잊어버렸어요. 어떻게 바꾸나요?',
    '아직도 답이 없네요. 벌써 세 번째 문의입니다. 최악이에요!!',
    '영업시간이 몇 시까지인가요?',
    '교환하고 싶은데 방법 알려주세요',
    '결제 영수증 다시 받을 수 있을까요'
  ].join('\n');

  var api = {
    OTHER_TEAM: OTHER_TEAM,
    DEFAULT_RULES: DEFAULT_RULES,
    DEFAULT_URGENCY: DEFAULT_URGENCY,
    SAMPLE_TEXT: SAMPLE_TEXT,
    clone: clone,
    normalize: normalize,
    splitInquiries: splitInquiries,
    classify: classify,
    urgency: urgency,
    levelRank: levelRank,
    processBatch: processBatch,
    groupByTeam: groupByTeam,
    summarize: summarize,
    rulesToText: rulesToText,
    parseRules: parseRules,
    urgencyToText: urgencyToText,
    parseUrgency: parseUrgency,
    toPlainText: toPlainText
  };

  root.InquiryCore = api;
})(typeof window !== 'undefined' ? window : globalThis);

if (typeof module !== 'undefined') module.exports = globalThis.InquiryCore;
