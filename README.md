<div align="center">

```
███████╗ ██████╗ ██████╗  ██████╗ ██████╗ ██╗   ██╗██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
██╔════╝██╔════╝██╔═══██╗██╔═══██╗██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
███████╗██║     ██║   ██║██║   ██║██████╔╝ ╚████╔╝ ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
╚════██║██║     ██║   ██║██║   ██║██╔══██╗  ╚██╔╝  ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
███████║╚██████╗╚██████╔╝╚██████╔╝██████╔╝   ██║   ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝    ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
```

**Unmask your machine's true AI performance with ONNX and Ollama benchmarks.**

[![Release](https://img.shields.io/github/v/release/yourusername/scoobybench?style=for-the-badge&color=F4A300&label=Latest+Release)](../../releases/latest)
[![License](https://img.shields.io/github/license/yourusername/scoobybench?style=for-the-badge&color=4A90D9)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?style=for-the-badge&logo=windows)](../../releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Node](https://img.shields.io/badge/Node.js-20%2B-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)

<br/>

> *"Scooby-Doo always reveals what's really going on behind the mask —*
> *just like ScoobyBench exposes the truth behind your AI hardware's claimed performance."*

<br/>

[**⬇ Download**](#installation) · [**📖 Documentation**](#usage) · [**🏗 Build from Source**](#building-from-source) · [**🤝 Contributing**](#contributing)

</div>

---

## What is ScoobyBench?

ScoobyBench is a **Windows desktop application** that runs reproducible AI inference workloads on your local machine, captures detailed system telemetry, and produces a clear **actual vs. claimed performance scorecard** — so you know exactly what your hardware can and cannot do, and why.

Vendors publish benchmark numbers under ideal, controlled conditions. Your laptop, with its thermal throttling, mixed driver versions, and real-world power limits, tells a different story. ScoobyBench tells *that* story — with evidence.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     YOUR MACHINE  vs  THE CLAIM                     │
│                                                                     │
│   Model: Llama-2-7B · Precision: FP16 · Repeats: 3                 │
│                                                                     │
│   Vendor Claim     ████████████████████████░░░░░░   82 tokens/sec  │
│   Your Result      ████████████████░░░░░░░░░░░░░░   54 tokens/sec  │
│                                                                     │
│   Delta: -34%  ·  Probable cause: Thermal throttling (91°C avg)     │
└─────────────────────────────────────────────────────────────────────┘
```

It is built with three hard constraints: **no cloud dependency**, **minimal background overhead**, and **privacy by default** — every byte of data stays on your machine unless you explicitly choose to share it.

---

## Features

Release `v2.0.0` includes:

- ONNX benchmark runs with saved JSON reports
- Local Ollama model benchmarking for pulled models such as `llama3` and `gemma4:e4b`
- Hardware-aware model recommendations
- System telemetry monitoring and report history
- Electron desktop UI backed by a local FastAPI service

```
┌──────────────────────┬─────────────────────────────────────────────────────────────────┐
│  🤖  AI Benchmarking │  Standardized inference workloads on ONNX models.               │
│                      │  Captures tokens/sec, p50/p90/p99 latency, VRAM, power.         │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│  📊  Live Telemetry  │  Real-time graphs for CPU, GPU, memory, temperature,             │
│                      │  power draw — streamed over WebSocket.                           │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│  🎯  Model Browser   │  Hardware-aware model recommendations. Compatible models         │
│                      │  highlighted; incompatible ones clearly flagged.                 │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│  📈  Gap Analysis    │  Compares your results to MLPerf baselines and vendor claims.    │
│                      │  Surfaces probable root causes: throttling, VRAM caps, drivers.  │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│  📄  Report Export   │  JSON reports with full environment snapshot. Shareable,         │
│                      │  reproducible, and structured for community baselines.           │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│  🔒  Privacy-First   │  All data is local by default. Optional anonymous upload         │
│                      │  requires explicit opt-in; no PII ever collected.                │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│  🖥  Native Windows  │  Single `.exe` installer with system tray, auto-updates,         │
│                      │  and portable mode — no dependencies to manage.                  │
└──────────────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Option 1 — Installer (Recommended)

Download `ScoobyBench Setup.exe` from the [**latest release**](../../releases/latest) and run it. The installer:

- Creates a desktop shortcut and Start Menu entry
- Registers a system tray icon for quick access
- Configures auto-update checks (opt-in)
- Requires no elevated privileges for standard use

### Option 2 — Portable

Download `ScoobyBench.exe` from the [**latest release**](../../releases/latest). Drop it anywhere and run it. No installation, no registry entries, no administrator access required. All data is written to the folder containing the executable.

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 64-bit | Windows 11 64-bit |
| RAM | 4 GB | 16 GB+ |
| GPU | None (CPU-only mode) | NVIDIA / AMD / Intel Arc |
| VRAM | N/A | 8 GB+ for 7B models |
| Storage | 500 MB | 5 GB+ (for model storage) |
| Drivers | Latest available | NVIDIA Game Ready / AMD Adrenalin |

> **Note:** GPU is optional. ScoobyBench runs entirely on CPU if no compatible GPU is present, but results will differ from GPU-accelerated baselines.

---

## Usage

### Running an ONNX Benchmark

```
1. Open ScoobyBench (system tray or desktop shortcut)
2. Navigate to the  [Benchmark]  tab
3. Select a model from the list (e.g., Llama-2-7B-Chat)
4. Choose precision: FP32 / FP16 / INT8
5. Click  [Start Benchmark]
6. Wait for pre-flight checks → warmup → timed inference
7. Review your scorecard: grade, tokens/sec, latency percentiles, power
8. Export the JSON report for sharing or archiving
```

### Running an Ollama Benchmark

```
1. Start Ollama locally with:  ollama serve
2. Pull a model such as:  ollama pull gemma4:e4b  or  ollama pull llama3
3. Navigate to the  [Ollama Benchmark]  tab
4. Confirm the local Ollama status shows as available
5. Select a pulled model from the list
6. Set prompt, max tokens, and repeats
7. Click  [Start Ollama Benchmark]
8. Review tokens/sec, latency, RAM use, CPU use, and the baseline comparison
```

### Monitoring System Telemetry

```
1. Navigate to the  [System Monitor]  tab
2. Click  [Start Monitoring]
3. Real-time graphs update every 5 seconds (configurable in Settings)
4. Run a benchmark in another tab — telemetry captures the impact live
5. Click  [Stop Monitoring]  to review historical stats
```

### Reading Your Report

A benchmark result gives you five key signals:

```
┌───────────────────────────────────────────────────────┐
│  PERFORMANCE GRADE                              B+     │
├───────────────────────────────────────────────────────┤
│  Tokens / sec          54.2    (baseline: 72.0)        │
│  Delta vs baseline    -24.7%                           │
│  p50 latency           18 ms                           │
│  p90 latency           31 ms                           │
│  p99 latency           58 ms                           │
├───────────────────────────────────────────────────────┤
│  Peak VRAM             6.4 GB                          │
│  Peak RAM              9.1 GB                          │
│  Avg power draw        87 W                            │
│  Tokens / sec / W      0.62                            │
├───────────────────────────────────────────────────────┤
│  ⚠ Probable cause: GPU sustained 89°C — thermal        │
│    throttle detected after 40s. Performance improved   │
│    by ~18% in repeat runs on a cooler system.          │
└───────────────────────────────────────────────────────┘
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ScoobyBench v2.0.0                                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Electron Frontend (React)                        │  │
│  │                                                                      │  │
│  │   [Benchmark Tab] [System Monitor] [Model Browser] [Reports] [⚙]   │  │
│  │                           │  WebSocket / REST                        │  │
│  └──────────────────────────┼───────────────────────────────────────────┘  │
│                             │                                               │
│  ┌──────────────────────────▼───────────────────────────────────────────┐  │
│  │                   FastAPI Backend  (:8472)                           │  │
│  │                                                                      │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐  │  │
│  │  │  Benchmark  │  │  Telemetry   │  │   Model    │  │  Report   │  │  │
│  │  │   Service   │  │   Agent      │  │  Registry  │  │  Engine   │  │  │
│  │  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └─────┬─────┘  │  │
│  │         │                │                 │               │         │  │
│  │  ┌──────▼──────┐  ┌──────▼───────┐  ┌─────▼──────┐        │         │  │
│  │  │ ONNX Runtime│  │ Perf Counters│  │ Baseline DB│  ┌─────▼──────┐  │  │
│  │  │  (Inference)│  │ NVML / ADL   │  │  (SQLite)  │  │  JSON/HTML │  │  │
│  │  └─────────────┘  └──────────────┘  └────────────┘  │   Export   │  │  │
│  │                                                      └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Role |
|-------|-----------|------|
| Frontend | Electron + React | Desktop UI, system tray, navigation |
| Backend | Python + FastAPI | REST API, WebSocket telemetry stream |
| Inference | ONNX Runtime | Model execution across CPU/GPU/NPU |
| Telemetry | Windows Perf Counters, NVML, ADL | Hardware sensor sampling |
| Storage | SQLite + JSON | Run history, settings, exports |
| Build | PyInstaller + electron-builder | Single `.exe` packaging |

---

## API Reference

The backend exposes a local REST API on `http://127.0.0.1:8472`. This is used internally by the UI, but you can call it directly for scripting or integration.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | `GET` | Backend health check |
| `/api/system/profile` | `GET` | Full hardware profile (CPU, GPU, RAM, drivers) |
| `/api/benchmark/run` | `POST` | Execute a benchmark run |
| `/api/benchmark/reports` | `GET` | List all saved reports |
| `/api/telemetry/start` | `POST` | Begin telemetry sampling |
| `/api/telemetry/samples` | `GET` | Retrieve telemetry history |
| `/api/models` | `GET` | List available models |
| `/api/models/recommendations` | `GET` | Hardware-matched model recommendations |
| `/api/ollama/status` | `GET` | Check whether local Ollama is reachable |
| `/api/ollama/models` | `GET` | List locally installed Ollama models |
| `/api/ollama/benchmark` | `POST` | Benchmark a locally running Ollama model |
| `/ws/telemetry` | `WebSocket` | Real-time telemetry stream |

**Example — run a benchmark via curl:**
```bash
curl -X POST http://127.0.0.1:8472/api/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{
    "model": {
      "name": "Llama-2-7B-Chat",
      "params_million": 7000,
      "precision": "fp16",
      "batch_size": 1,
      "prompt_tokens": 128,
      "target_tokens": 256,
      "repeats": 3
    }
  }'
```

---

## Report JSON Schema

Every benchmark produces a structured JSON report with the following shape:

```jsonc
{
  "run_id": "sbench_20250514_143022",
  "timestamp": "2025-05-14T14:30:22Z",
  "device": {
    "os": "Windows 11 23H2",
    "cpu": "Intel Core i9-13900H",
    "gpu": "NVIDIA RTX 4060 Laptop",
    "ram_gb": 32,
    "vram_gb": 8,
    "driver_versions": "551.86"
  },
  "model": {
    "name": "Llama-2-7B-Chat",
    "precision": "fp16",
    "batch_size": 1,
    "prompt_tokens": 128
  },
  "metrics": {
    "latency_ms": { "p50": 18, "p90": 31, "p99": 58 },
    "tokens_per_sec": 54.2,
    "peak_ram_mb": 9318,
    "peak_vram_mb": 6553,
    "avg_power_w": 87.4,
    "cpu_util_pct": 42.1,
    "gpu_util_pct": 96.8
  },
  "comparator": {
    "baseline_source": "MLPerf v4.0",
    "baseline_tokens_per_sec": 72.0,
    "delta_pct": -24.7
  }
}
```

---

## Building from Source

### Prerequisites

- Python 3.10 or later
- Node.js 20 or later
- Git
- Windows 10/11 (hardware detection APIs are Windows-only)

### Step 1 — Clone

```powershell
git clone https://github.com/06pratyush/ScoobyBench-ai_benchmarking_system
cd scoobybench
```

### Step 2 — Backend Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Frontend Setup

```powershell
cd ..\frontend
npm install
```

### Step 4 — Run in Development Mode

```powershell
# Terminal 1 — Backend
cd backend && python run.py
# Starts on http://127.0.0.1:8472

# Terminal 2 — Frontend
cd frontend && npm run electron:dev
# Opens the Electron window connected to the local backend
```

### Step 5 — Build Production Release

```powershell
cd scripts
python build_installer.py
# Outputs:
#   frontend/dist/ScoobyBench Setup.exe   ← Installer
#   frontend/dist/ScoobyBench.exe         ← Portable
```

---

## Versioning & Roadmap

ScoobyBench uses [Semantic Versioning](https://semver.org) (`MAJOR.MINOR.PATCH`).

```
v2.0.0  ← Current stable release
│
├── v1.x   CLI runner · ONNX inference · Telemetry · JSON reports · GitHub Releases
├── v2.x   GUI scorecard · ONNX + Ollama benchmarking · Reports · Model recommendations
├── v3.x   Auto-update · Scheduled benchmarks · Team sharing · Plugin system
└── v4.x   Enterprise: fleet dashboards · SSO · Centralized baseline server
```

---

## Privacy & Security

ScoobyBench is designed to be **safe to run on any machine**, including corporate hardware.

- **Local by default.** All benchmark results, telemetry, and reports are stored in SQLite on your device. Nothing leaves your machine without an explicit action from you.
- **No PII collected.** If you enable optional anonymous uploads, hardware serials and identifiers are stripped before transmission. Only aggregated metrics are sent.
- **Signed binaries.** Release executables are code-signed. Your OS will verify the signature before execution.
- **No background services by default.** ScoobyBench does not install persistent background processes unless you explicitly enable the telemetry agent.
- **Transparent retention.** Default run history retention is 30 days. Configurable in Settings.

---

## Troubleshooting

**Backend won't start / connection refused**
Check that port 8472 is free: `netstat -ano | findstr 8472`. If something else is using it, stop that process or change ScoobyBench's port in `config/settings.json`.

**GPU not detected**
Run `nvidia-smi` (NVIDIA) or check AMD Adrenalin is installed. Update GPU drivers to the latest release. Restart ScoobyBench after driver updates.

**Results vary significantly between runs**
Ensure your machine is on the **High Performance** power plan (Settings → Power → High Performance). Close background applications, particularly browsers and other GPU consumers, before benchmarking.

**High memory usage during idle**
Reduce telemetry retention: Settings → Telemetry → Retention Days → set to 7. The benchmarking runtime is unloaded immediately after each run; idle memory usage should be under 50 MB.

**"PyInstaller not found" during build**
```powershell
pip install pyinstaller
```

---

## Contributing

Contributions are welcome — bug reports, baseline submissions, new model integrations, and UI improvements all help.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit with a descriptive message following [Conventional Commits](https://www.conventionalcommits.org/)
4. Push and open a Pull Request

For baseline data submissions (your JSON reports to improve the comparator), open a Discussion thread under **Community Baselines**.

See [docs/API.md](docs/API.md) for backend API documentation and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

---

## Acknowledgments

- [ONNX Runtime](https://onnxruntime.ai/) — cross-platform model inference engine
- [MLPerf](https://mlcommons.org/) — standardized AI benchmarking methodology and reference numbers
- [Electron](https://www.electronjs.org/) + [React](https://react.dev/) — desktop UI framework
- [FastAPI](https://fastapi.tiangolo.com/) — Python backend framework
- [PyInstaller](https://pyinstaller.org/) — Python executable packaging

---

## License

ScoobyBench is released under the [MIT License](LICENSE). You are free to use, modify, and distribute it for any purpose, including commercial use, with attribution.

---

<div align="center">

**Built to tell the truth about your hardware.**

[⬇ Download v2.0.0](../../releases/latest) · [🐛 Report a Bug](../../issues) · [💬 Discussions](../../discussions)

</div>
