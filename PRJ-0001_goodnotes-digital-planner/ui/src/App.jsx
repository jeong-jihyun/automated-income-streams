import React, { useState } from 'react'

// 설정 검증: engine/config.py 와 같은 규칙을 화면에서도 먼저 확인한다.
export function validate(s) {
  const errors = []
  if (!Number.isInteger(s.year) || s.year < 2000 || s.year > 2100) errors.push('연도는 2000~2100 사이여야 합니다')
  if (s.notes < 0 || s.notes > 50) errors.push('노트 페이지는 0~50')
  return errors
}

const THEMES = { navy: '#1F3864', sage: '#5B7F6A', rose: '#B45A6E', mono: '#333333' }

export default function App() {
  const [s, setS] = useState({ year: 2027, weekStart: 'monday', lang: 'ko', theme: 'navy', weekly: true, daily: true, notes: 5 })
  const [log, setLog] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k, v) => setS({ ...s, [k]: v })
  const errors = validate(s)

  async function generate() {
    if (errors.length) return
    setBusy(true); setLog('생성 중...')
    try {
      // Electron preload(window.planner)가 있으면 Python 엔진 실행, 없으면 명령어만 보여 준다.
      if (window.planner) setLog(JSON.stringify(await window.planner.generate(s), null, 2))
      else setLog(`브라우저에서는 실행할 수 없습니다. 터미널에서:\npython -m engine.cli --year ${s.year} --lang ${s.lang} --theme ${s.theme} --week-start ${s.weekStart}`)
    } catch (e) { setLog('오류: ' + e.message) }
    setBusy(false)
  }

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 560, margin: '24px auto', padding: 16 }}>
      <h1>굿노트 플래너 생성기</h1>
      <label>연도 <input type="number" value={s.year} onChange={e => set('year', Number(e.target.value))} /></label><br />
      <label>주 시작 요일 <select value={s.weekStart} onChange={e => set('weekStart', e.target.value)}>
        <option value="monday">월요일</option><option value="sunday">일요일</option></select></label><br />
      <label>언어 <select value={s.lang} onChange={e => set('lang', e.target.value)}>
        <option value="ko">한국어</option><option value="en">English</option></select></label><br />
      <div>테마 {Object.entries(THEMES).map(([k, c]) => (
        <button key={k} onClick={() => set('theme', k)} aria-label={k}
          style={{ background: c, width: 28, height: 28, marginRight: 6, border: s.theme === k ? '3px solid #FFC000' : '1px solid #888' }} />))}</div>
      <label><input type="checkbox" checked={s.weekly} onChange={e => set('weekly', e.target.checked)} /> 주간 페이지</label>{' '}
      <label><input type="checkbox" checked={s.daily} onChange={e => set('daily', e.target.checked)} /> 일간 페이지</label><br />
      <label>노트 페이지 수 <input type="number" value={s.notes} onChange={e => set('notes', Number(e.target.value))} /></label>
      {errors.map(m => <p key={m} style={{ color: '#B00020' }}>{m}</p>)}
      <p><button disabled={busy || errors.length > 0} onClick={generate}>PDF 만들기</button></p>
      <pre style={{ background: '#F4F4F4', padding: 8, whiteSpace: 'pre-wrap' }}>{log}</pre>
    </main>
  )
}
