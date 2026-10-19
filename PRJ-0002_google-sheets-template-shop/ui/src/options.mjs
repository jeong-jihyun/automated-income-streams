// 화면 선택값을 CLI 명령으로 바꾼다. engine/presets.py 와 같은 값만 허용한다.
export const KINDS = { budget: '가계부', project: '프로젝트 관리', inventory: '재고 관리' }
export const JOBS = { freelancer: '프리랜서', shop_owner: '소상공인', student: '학생' }
export const THEMES = { navy: '#1F3864', sage: '#5B7F6A', rose: '#B45A6E' }

export function buildCommand({ kind, job, theme }) {
  if (!(kind in KINDS)) throw new Error('템플릿 종류 오류')
  if (!(job in JOBS)) throw new Error('직무 오류')
  if (!(theme in THEMES)) throw new Error('테마 오류')
  return `python -m engine.cli --kind ${kind} --job ${job} --theme ${theme} --out output`
}

export function fileName({ kind, job, theme }) { return `${kind}_${job}_${theme}.xlsx` }
