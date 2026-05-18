const { app, BrowserWindow, ipcMain, dialog, shell, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const net = require('net');

const IS_DEV = !app.isPackaged;
const API_PORT = 8472;

let mainWindow = null;
let tray = null;
let backendProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'ScoobyBench',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: path.join(__dirname, 'preload.js'),
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
      webSecurity: true
    },
    show: false
  });

  if (IS_DEV) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    const indexPath = path.join(__dirname, '..', '..', 'dist', 'index.html');
    mainWindow.loadFile(indexPath);
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('close', (event) => {
    if (tray && !app.isQuiting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(true));
    server.once('listening', () => {
      server.close();
      resolve(false);
    });
    server.listen(port, '127.0.0.1');
  });
}

function findBackendPath() {
  const candidates = [
    path.join(process.resourcesPath, 'backend', 'run.py'),
    path.join(__dirname, '..', '..', '..', 'backend', 'run.py'),
    path.join(__dirname, '..', '..', 'backend', 'run.py'),
    path.join(process.cwd(), '..', 'backend', 'run.py'),
    path.join(process.cwd(), 'backend', 'run.py')
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      console.log('[Main] Found backend at:', candidate);
      return candidate;
    }
  }
  console.error('[Main] Backend not found in any location');
  return null;
}

function findPythonExecutable(scriptPath) {
  const repoRoot = path.resolve(path.dirname(scriptPath), '..');
  const backendRoot = path.dirname(scriptPath);
  const candidates = [
    path.join(backendRoot, 'venv311', 'Scripts', 'python.exe'),
    path.join(backendRoot, 'venv', 'Scripts', 'python.exe'),
    path.join(repoRoot, '.venv', 'Scripts', 'python.exe'),
    path.join(repoRoot, 'venv311', 'Scripts', 'python.exe'),
    path.join(repoRoot, 'venv', 'Scripts', 'python.exe'),
    'python'
  ];

  for (const candidate of candidates) {
    if (candidate === 'python' || fs.existsSync(candidate)) {
      console.log('[Main] Using Python runtime:', candidate);
      return candidate;
    }
  }

  return 'python';
}

async function startBackend() {
  const alreadyRunning = await isPortInUse(API_PORT);
  if (alreadyRunning) {
    console.log('[Main] Backend already running on port', API_PORT);
    return;
  }

  const scriptPath = findBackendPath();
  if (!scriptPath) {
    console.error('[Main] Cannot start backend: run.py not found');
    return;
  }

  const pythonExecutable = findPythonExecutable(scriptPath);
  console.log('[Main] Starting backend:', scriptPath);
  backendProcess = spawn(pythonExecutable, [scriptPath], {
    cwd: path.dirname(scriptPath),
    stdio: 'pipe',
    env: { ...process.env, PYTHONPATH: path.dirname(scriptPath) }
  });

  backendProcess.stdout.on('data', (data) => console.log('[Backend]', data.toString().trim()));
  backendProcess.stderr.on('data', (data) => console.error('[Backend]', data.toString().trim()));
  backendProcess.on('close', (code) => console.log('[Main] Backend exited with code', code));
}

function createTray() {
  // Create a 16x16 blank transparent image as fallback
  const emptyIcon = nativeImage.createEmpty();
  
  try {
    tray = new Tray(emptyIcon);
  } catch (e) {
    console.log('[Main] Tray creation failed:', e.message);
    return; // Skip tray if it fails
  }

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show ScoobyBench', click: () => mainWindow && mainWindow.show() },
    { label: 'Run Benchmark', click: () => {
      if (mainWindow) {
        mainWindow.show();
        mainWindow.webContents.send('navigate', 'benchmark');
      }
    }},
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuiting = true; app.quit(); }}
  ]);

  tray.setToolTip('ScoobyBench');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
}

// IPC Handlers
ipcMain.handle('api:get', async (event, endpoint) => {
  try {
    const response = await fetch(`http://127.0.0.1:${API_PORT}${endpoint}`);
    return await response.json();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('api:post', async (event, endpoint, data) => {
  try {
    const response = await fetch(`http://127.0.0.1:${API_PORT}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await response.json();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [{ name: 'ONNX Models', extensions: ['onnx'] }, { name: 'All Files', extensions: ['*'] }]
  });
  return result.filePaths[0] || null;
});

ipcMain.handle('dialog:saveFile', async (event, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: defaultName,
    filters: [{ name: 'JSON Report', extensions: ['json'] }, { name: 'All Files', extensions: ['*'] }]
  });
  return result.filePath || null;
});

ipcMain.handle('fs:writeTextFile', async (event, filePath, content) => {
  await fs.promises.writeFile(filePath, content, 'utf8');
  return true;
});

ipcMain.handle('shell:openExternal', async (event, url) => {
  await shell.openExternal(url);
});

ipcMain.handle('app:getVersion', () => app.getVersion());

// App lifecycle
app.whenReady().then(async () => {
  await startBackend();

  setTimeout(() => {
    createWindow();
    createTray();
  }, 1500);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on('before-quit', () => {
  app.isQuiting = true;
  if (backendProcess) backendProcess.kill();
});

app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});
