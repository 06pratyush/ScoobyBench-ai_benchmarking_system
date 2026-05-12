# ScoobyBench - Complete Build & Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Building the Application](#building-the-application)
4. [Testing](#testing)
5. [Deployment](#deployment)
6. [GitHub Releases](#github-releases)

## Prerequisites

### Required Software
- **Windows 10/11** (for full hardware detection support)
- **Python 3.10+** with pip
- **Node.js 20+** with npm
- **Git** for version control

### Optional but Recommended
- **Visual Studio Build Tools** (for native Python modules)
- **Windows SDK** (for code signing)
- **Code Signing Certificate** (for trusted distribution)

## Development Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/scoobybench.git
cd scoobybench
```

### Step 2: Setup Python Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio httpx
```

### Step 3: Setup Node Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Install global tools (optional)
npm install -g electron
```

### Step 4: Verify Setup
```bash
# Test backend (Terminal 1)
cd backend
python run.py
# Should start on http://127.0.0.1:8472

# Test frontend (Terminal 2)
cd frontend
npm run start
# Should open browser at http://localhost:3000
```

## Building the Application

### Method 1: Automated Build (Recommended)
```bash
cd scripts
python build_installer.py
```

This script:
1. Cleans previous builds
2. Packages Python backend with PyInstaller
3. Builds Electron frontend
4. Packages everything into single installer

### Method 2: Manual Build

#### Build Backend
```bash
cd backend

# Install PyInstaller
pip install pyinstaller

# Create spec file
pyi-makespec --onefile run.py

# Edit run.spec to include app/ directory and hidden imports
# Then build:
pyinstaller run.spec --clean --noconfirm

# Output: dist/run.exe
```

#### Build Frontend
```bash
cd frontend

# Build for production
npm run build

# Package with electron-builder
npm run dist:win

# Output: dist/ScoobyBench Setup.exe, dist/ScoobyBench.exe
```

#### Combine
```bash
# Copy backend executable to frontend resources
mkdir -p frontend/dist/backend
cp backend/dist/run.exe frontend/dist/backend/

# Rebuild with resources
npm run dist:win
```

### Build Outputs
After successful build, you'll find:
- `frontend/dist/ScoobyBench Setup.exe` - NSIS installer
- `frontend/dist/ScoobyBench.exe` - Portable version
- `frontend/dist/win-unpacked/` - Unpacked files

## Testing

### Unit Tests
```bash
cd backend
pytest tests/ -v --tb=short
```

### Integration Tests
```bash
# Start backend
cd backend && python run.py

# Run API tests
curl http://127.0.0.1:8472/api/health
curl http://127.0.0.1:8472/api/system/profile
```

### Manual Testing Scenarios

#### Scenario 1: Fresh Install
1. Uninstall any previous version
2. Run `ScoobyBench Setup.exe`
3. Verify desktop shortcut created
4. Launch from Start Menu
5. Check system tray icon appears

#### Scenario 2: Benchmark Workflow
1. Open Benchmark tab
2. Select "Llama-2-7B-Chat" model
3. Set precision to FP16
4. Click Start Benchmark
5. Verify progress updates
6. Check results show grade, tokens/sec, latency
7. Export JSON report
8. Verify file saved correctly

#### Scenario 3: Telemetry Monitoring
1. Open System Monitor tab
2. Click Start Monitoring
3. Verify real-time graphs update
4. Check WebSocket connection status
5. Run a benchmark while monitoring
6. Verify telemetry shows benchmark impact
7. Stop monitoring
8. Check historical stats

#### Scenario 4: Model Recommendations
1. Open Model Browser
2. Verify recommendations match hardware
3. Check incompatible models show red
4. Click Benchmark on a compatible model
5. Verify navigation to Benchmark tab

#### Scenario 5: Report Management
1. Run 3+ benchmarks
2. Open Reports tab
3. Verify all reports listed
4. Click a report for details
5. Check latency distribution
6. Export a report
7. Verify JSON structure

#### Scenario 6: Settings Persistence
1. Open Settings tab
2. Change telemetry interval to 10s
3. Close and reopen app
4. Verify setting persisted

#### Scenario 7: Portable Mode
1. Copy `ScoobyBench.exe` to new folder
2. Run without installation
3. Verify all features work
4. Check no registry entries created

#### Scenario 8: Error Handling
1. Disconnect from backend (kill process)
2. Try to run benchmark
3. Verify graceful error message
4. Restart backend
5. Verify auto-reconnection

### Performance Testing
```bash
# Run benchmark 10 times for consistency
cd backend
python -c "
import requests
for i in range(10):
    r = requests.post('http://127.0.0.1:8472/api/benchmark/run', json={
        'model': {
            'name': 'test',
            'params_million': 1000,
            'precision': 'fp16',
            'batch_size': 1,
            'prompt_tokens': 128,
            'target_tokens': 256,
            'repeats': 3
        }
    })
    print(f'Run {i+1}: {r.json()["metrics"]["tokens_per_sec"]:.2f} t/s')
"
```

### Load Testing
```bash
# Test concurrent requests
ab -n 100 -c 10 http://127.0.0.1:8472/api/health
```

## Deployment

### Local Distribution
```bash
# Copy installer to shared drive
xcopy frontend\dist\ScoobyBench*.exe \\server\share\ /Y
```

### GitHub Releases

#### Method 1: Automated (CI/CD)
1. Push tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```
2. GitHub Actions automatically builds and creates draft release
3. Review release notes
4. Publish release

#### Method 2: Manual
1. Build locally:
```bash
cd scripts
python build_installer.py
```
2. Create release on GitHub
3. Upload assets:
```bash
cd scripts
set GITHUB_TOKEN=your_token_here
python release.py
```

### Auto-Update Configuration

In `frontend/package.json`:
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "yourusername",
      "repo": "scoobybench"
    }
  }
}
```

In `frontend/src/main/main.js`:
```javascript
const { autoUpdater } = require('electron-updater');

// Check for updates
autoUpdater.checkForUpdatesAndNotify();

autoUpdater.on('update-available', () => {
  console.log('Update available');
});

autoUpdater.on('update-downloaded', () => {
  autoUpdater.quitAndInstall();
});
```

### Code Signing (Production)

```bash
# Sign installer
cd scripts
python sign_binary.py \
  "../frontend/dist/ScoobyBench Setup.exe" \
  "path/to/certificate.pfx" \
  "certificate_password"

# Sign portable
python sign_binary.py \
  "../frontend/dist/ScoobyBench.exe" \
  "path/to/certificate.pfx" \
  "certificate_password"
```

## Troubleshooting

### Build Issues

**"PyInstaller not found"**
```bash
pip install pyinstaller
```

**"npm install fails"**
```bash
# Clear cache
npm cache clean --force
# Use yarn instead
npm install -g yarn
yarn install
```

**"Electron build fails"**
```bash
# Rebuild native modules
npm rebuild
# Or
npm install --build-from-source
```

### Runtime Issues

**"Backend connection refused"**
- Check port 8472 is not in use: `netstat -ano | findstr 8472`
- Check Windows Firewall settings
- Run backend manually: `cd backend && python run.py`

**"GPU not detected"**
- Update GPU drivers
- For NVIDIA: `nvidia-smi` should work in terminal
- For AMD: Check Adrenalin software installed

**"High memory usage"**
- Reduce telemetry retention: Settings > Telemetry > Retention Days
- Close other applications during benchmarks

## Security Checklist

- [ ] Code signing certificate obtained
- [ ] Binaries signed before distribution
- [ ] GitHub token stored as secret (not in code)
- [ ] No hardcoded credentials
- [ ] CSP headers configured in HTML
- [ ] Context isolation enabled in Electron
- [ ] No nodeIntegration in renderer
- [ ] Auto-updater uses HTTPS
- [ ] Anonymous data only (no PII)

## Versioning

Follow Semantic Versioning:
- `MAJOR.MINOR.PATCH`
- Example: `1.0.0` -> `1.1.0` (new feature) -> `1.1.1` (bugfix)

Update version in:
- `frontend/package.json`
- `backend/app/config.py`
- Git tag
