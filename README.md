# 🐕 ScoobyBench

> *"Scooby-Doo always reveals what's really going on behind the mask, just like your app exposes real vs claimed AI performance."*

**ScoobyBench** is a Windows desktop application that benchmarks locally-running AI models, tracks system telemetry in real-time, and provides actionable insights about your hardware's AI capabilities.

## Features

- 🤖 **AI Model Benchmarking** - Test ONNX models with standardized metrics (tokens/sec, latency, memory)
- 📊 **Real-time Telemetry** - Monitor CPU, GPU, memory, temperature, and power consumption
- 🎯 **Model Recommendations** - Get AI model suggestions based on your hardware profile
- 📈 **Performance Comparison** - Compare results against MLPerf baselines and vendor claims
- 🔒 **Privacy-First** - All data stays local; optional anonymous uploads
- 🖥️ **Native Windows App** - Single .exe installer with auto-updates via GitHub Releases

## Quick Start

### Download
Download the latest release from [GitHub Releases](../../releases):
- **Installer** (`ScoobyBench Setup.exe`) - Recommended for most users
- **Portable** (`ScoobyBench.exe`) - Run without installation

### System Requirements
- Windows 10/11 64-bit
- 4GB RAM minimum (8GB+ recommended for large models)
- GPU optional (NVIDIA/AMD/Intel supported)

### Usage
1. Install or run the portable version
2. The app auto-starts the backend server
3. Use the system tray icon or desktop shortcut to open
4. Run benchmarks from the **Benchmark** tab
5. Monitor your system from the **System Monitor** tab

## Development

### Prerequisites
- Python 3.10+
- Node.js 20+
- Windows (for full hardware detection)

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/scoobybench.git
cd scoobybench

# Setup backend
cd backend
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
```

### Running in Development
```bash
# Terminal 1: Start backend
cd backend
python run.py

# Terminal 2: Start frontend
cd frontend
npm run electron:dev
```

### Building
```bash
# Build complete application
cd scripts
python build_installer.py

# Or manually:
# 1. Build backend: pyinstaller backend.spec
# 2. Build frontend: cd frontend && npm run dist:win
```

## Architecture

```
ScoobyBench/
├── backend/           # Python FastAPI server
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── api/routes.py     # REST API endpoints
│   │   ├── services/         # Benchmark, telemetry, models
│   │   └── utils/            # Hardware detection
│   └── requirements.txt
├── frontend/          # Electron + React desktop app
│   ├── src/main/      # Electron main process
│   └── src/renderer/  # React UI components
├── config/            # Baselines and default settings
└── scripts/           # Build and release automation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/system/profile` | GET | Hardware profile |
| `/api/benchmark/run` | POST | Run benchmark |
| `/api/benchmark/reports` | GET | List reports |
| `/api/telemetry/start` | POST | Start monitoring |
| `/api/telemetry/samples` | GET | Get samples |
| `/api/models` | GET | List models |
| `/api/models/recommendations` | GET | Get recommendations |
| `/ws/telemetry` | WS | Real-time telemetry stream |

## Telemetry Data

ScoobyBench collects:
- CPU utilization (%)
- Memory usage (% and MB)
- GPU utilization and VRAM (if available)
- Temperature (if sensors available)
- Power consumption (if available)
- Running process detection

All data is stored locally in SQLite. No data leaves your machine unless you explicitly enable uploads.

## Benchmarking Methodology

1. **Pre-flight checks** - Validate system state and model availability
2. **Warmup** - Stabilize CPU/GPU clocks
3. **Timed inference** - Run model for configured token count
4. **Repeat** - Multiple runs for statistical significance
5. **Normalization** - Adjust for precision, batch size, prompt length
6. **Comparison** - Compare against baselines and generate grade

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

See [docs/API.md](docs/API.md) for API documentation.

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- Built with [ONNX Runtime](https://onnxruntime.ai/) for model inference
- Telemetry inspired by [MLPerf](https://mlcommons.org/) standards
- UI built with [Electron](https://www.electronjs.org/) and [React](https://react.dev/)
