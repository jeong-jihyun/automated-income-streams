const { contextBridge, ipcRenderer } = require('electron')
contextBridge.exposeInMainWorld('planner', { generate: (settings) => ipcRenderer.invoke('planner:generate', settings) })
