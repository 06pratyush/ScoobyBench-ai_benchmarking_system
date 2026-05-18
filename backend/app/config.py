"""ScoobyBench Configuration Module"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

APP_NAME = "ScoobyBench"
APP_VERSION = "2.0.0"
APP_DIR = Path(os.environ.get("SCOOBYBENCH_HOME", Path.home() / ".scoobybench"))
APP_DIR.mkdir(exist_ok=True)

@dataclass
class AppConfig:
    """Application configuration"""
    # Paths
    data_dir: Path = APP_DIR / "data"
    models_dir: Path = APP_DIR / "models"
    reports_dir: Path = APP_DIR / "reports"
    logs_dir: Path = APP_DIR / "logs"

    # Server
    host: str = "127.0.0.1"
    port: int = 8472  # SB on keypad

    # Telemetry
    telemetry_interval: float = 5.0  # seconds
    telemetry_retention_days: int = 30
    max_telemetry_samples: int = 100000

    # Benchmarking
    default_repeats: int = 3
    warmup_tokens: int = 50
    max_test_duration: int = 300  # 5 minutes

    # Models
    bundled_models: Dict[str, Any] = None
    max_model_size_gb: float = 10.0

    # Privacy
    upload_enabled: bool = False
    anonymize: bool = True

    # UI
    auto_start_monitor: bool = False
    minimize_to_tray: bool = True

    def __post_init__(self):
        if self.bundled_models is None:
            self.bundled_models = {
                "llama2-7b-chat": {
                    "name": "Llama-2-7B-Chat",
                    "source": "huggingface",
                    "params_million": 7000,
                    "recommended_precision": "fp16",
                    "min_vram_gb": 8,
                    "min_ram_gb": 16,
                    "url": "https://huggingface.co/meta-llama/Llama-2-7b-chat-hf"
                },
                "phi-2": {
                    "name": "Phi-2",
                    "source": "huggingface", 
                    "params_million": 2700,
                    "recommended_precision": "fp16",
                    "min_vram_gb": 4,
                    "min_ram_gb": 8,
                    "url": "https://huggingface.co/microsoft/phi-2"
                }
            }
        # Ensure directories exist
        for d in [self.data_dir, self.models_dir, self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {k: str(v) if isinstance(v, Path) else v for k, v in asdict(self).items()}

    def save(self, path: Optional[Path] = None):
        path = path or APP_DIR / "config.json"
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AppConfig":
        path = path or APP_DIR / "config.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            # Convert string paths back to Path objects
            for key in ['data_dir', 'models_dir', 'reports_dir', 'logs_dir']:
                if key in data and isinstance(data[key], str):
                    data[key] = Path(data[key])
            return cls(**data)
        return cls()

# Global config instance
config = AppConfig.load()
