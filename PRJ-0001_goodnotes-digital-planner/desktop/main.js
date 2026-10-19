const { app, BrowserWindow, ipcMain } = require('electron')
const { execFile } = require('child_process')
const path = require('path')
const root = path.join(__dirname, '..')

// 화면에서 받은 설정을 Python 엔진 인자로 바꾼다. 허용된 값만 통과시킨다.
function toArgs(s) {
  const year = Number(s.year)
  if (!Number.isInteger(year) || year < 2000 || year > 2100) throw new Error('연도 오류')
  if (!['monday', 'sunday'].includes(s.weekStart)) throw new Error('요일 오류')
  if (!['ko', 'en'].includes(s.lang)) throw new Error('언어 오류')
  if (!['navy', 'sage', 'rose', 'mono'].includes(s.theme)) throw new Error('테마 오류')
  const notes = Number(s.notes)
  if (!Number.isInteger(notes) || notes < 0 || notes > 50) throw new Error('노트 수 오류')
  const a = ['-m', 'engine.cli', '--year', String(year), '--week-start', s.weekStart, '--lang', s.lang,
    '--theme', s.theme, '--notes', String(notes), '--out', path.join(app.getPath('documents'), 'planner_output')]
  if (!s.weekly) a.push('--no-weekly')
  if (!s.daily) a.push('--no-daily')
  return a
}

ipcMain.handle('planner:generate', (_e, s) => new Promise((resolve, reject) => {
  let args
  try { args = toArgs(s) } catch (e) { return reject(e) }
  execFile(process.platform === 'win32' ? 'python' : 'python3', args, { cwd: root }, (err, out, errout) => {
    if (err) reject(new Error(errout || err.message)); else resolve(JSON.parse(out))
  })
}))

app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 760, height: 720,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true } })
  win.loadFile(path.join(root, 'ui', 'dist', 'index.html'))
})
app.on('window-all-closed', () => app.quit())
