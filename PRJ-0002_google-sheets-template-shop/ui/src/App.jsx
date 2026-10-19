import React, { useState } from 'react'
import { KINDS, JOBS, THEMES, buildCommand, fileName } from './options.mjs'

export default function App() {
  const [s, setS] = useState({ kind: 'budget', job: 'freelancer', theme: 'navy' })
  const [copied, setCopied] = useState(false)
  const cmd = buildCommand(s)
  const pick = (k, v) => { setS({ ...s, [k]: v }); setCopied(false) }
  const Row = ({ label, field, items }) => (
    <p><b>{label}</b><br />{Object.entries(items).map(([k, v]) => (
      <button key={k} onClick={() => pick(field, k)} style={{ marginRight: 6, padding: '6px 10px',
        background: s[field] === k ? '#1F3864' : '#EEE', color: s[field] === k ? '#FFF' : '#222', border: 0, borderRadius: 4 }}>
        {typeof v === 'string' && v.startsWith('#') ? k : v}</button>))}</p>)
  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 600, margin: '24px auto', padding: 16 }}>
      <h1>구글 시트 템플릿 생성기</h1>
      <Row label="1. 템플릿 종류" field="kind" items={KINDS} />
      <Row label="2. 직무" field="job" items={JOBS} />
      <Row label="3. 색상" field="theme" items={THEMES} />
      <h3>만들어질 파일: {fileName(s)}</h3>
      <p>터미널에서 아래 명령을 실행하면 파일이 만들어지고, 수식 검사까지 자동으로 합니다.</p>
      <pre style={{ background: '#F4F4F4', padding: 10, whiteSpace: 'pre-wrap' }}>{cmd}</pre>
      <button onClick={async () => { await navigator.clipboard.writeText(cmd); setCopied(true) }}>
        {copied ? '복사됨 ✓' : '명령어 복사'}</button>
    </main>
  )
}
