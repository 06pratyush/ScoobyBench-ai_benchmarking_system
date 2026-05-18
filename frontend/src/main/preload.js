const { contextBridge, ipcRenderer } = require('electron');

// Secure API exposed to renderer
// Following 2026 best practices: contextIsolation + contextBridge
contextBridge.exposeInMainWorld('electronAPI', {
  // API calls
  apiGet: (endpoint) => ipcRenderer.invoke('api:get', endpoint),
  apiPost: (endpoint, data) => ipcRenderer.invoke('api:post', endpoint, data),

  // File dialogs
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (defaultName) => ipcRenderer.invoke('dialog:saveFile', defaultName),
  writeTextFile: (filePath, content) => ipcRenderer.invoke('fs:writeTextFile', filePath, content),

  // System
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  getVersion: () => ipcRenderer.invoke('app:getVersion'),

  // Navigation
  onNavigate: (callback) => ipcRenderer.on('navigate', (_event, page) => callback(page)),

  // WebSocket helper
  getApiUrl: () => 'http://127.0.0.1:8472',
  getWsUrl: () => 'ws://127.0.0.1:8472/ws/telemetry'
});
