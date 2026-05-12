# Installation Guide

## Windows (Recommended)

### Option 1: Installer (Recommended)
1. Download `ScoobyBench Setup.exe` from [GitHub Releases](../../releases)
2. Run the installer
3. Follow the setup wizard
4. Launch from Start Menu or Desktop shortcut

### Option 2: Portable
1. Download `ScoobyBench.exe` from [GitHub Releases](../../releases)
2. Place in any folder (e.g., `C:\Tools\ScoobyBench`)
3. Double-click to run
4. No installation required

### Option 3: Build from Source
```bash
# Prerequisites
# - Python 3.10+
# - Node.js 20+
# - Windows 10/11

# 1. Clone repository
git clone https://github.com/yourusername/scoobybench.git
cd scoobybench

# 2. Setup Python backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Setup Node frontend
cd ../frontend
npm install

# 4. Run in development
# Terminal 1:
cd ../backend
python run.py

# Terminal 2:
cd ../frontend
npm run electron:dev

# 5. Build for production
cd ../scripts
python build_installer.py
```

## First Run

After installation:
1. ScoobyBench will appear in your system tray
2. Click the tray icon or desktop shortcut to open
3. The backend server starts automatically
4. Wait for the "System Ready" indicator

## Troubleshooting

### "Backend connection failed"
- Check if port 8472 is available
- Restart the application
- Check Windows Defender/firewall settings

### "ONNX Runtime not found"
- Install Visual C++ Redistributable 2022
- Reinstall with `pip install onnxruntime`

### "GPU not detected"
- Update GPU drivers
- For NVIDIA: Install CUDA toolkit (optional)
- For AMD: Ensure ROCm is not required for basic detection

### "Telemetry not starting"
- Run as Administrator for full hardware access
- Check if WMI service is running
