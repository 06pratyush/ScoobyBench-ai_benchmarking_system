"""Pydantic schemas for API validation"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class Precision(str, Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"
    INT4 = "int4"

class DeviceInfo(BaseModel):
    os: str
    os_build: str
    cpu: str
    cpu_cores: int
    cpu_threads: int
    gpu: Optional[str] = None
    gpu_vram_gb: Optional[float] = None
    npu: Optional[str] = None
    ram_gb: float
    driver_versions: Dict[str, str] = Field(default_factory=dict)
    power_plan: str
    bios_version: str

class ModelConfig(BaseModel):
    name: str
    onnx_path: Optional[str] = None
    params_million: int
    precision: Precision = Precision.FP16
    batch_size: int = 1
    prompt_tokens: int = 128
    target_tokens: int = 512
    repeats: int = 3

class BenchmarkRequest(BaseModel):
    model: ModelConfig
    device_info: Optional[DeviceInfo] = None

class LatencyMetrics(BaseModel):
    p50_ms: float
    p90_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float

class BenchmarkMetrics(BaseModel):
    latency: LatencyMetrics
    tokens_per_sec: float
    peak_ram_mb: float
    peak_vram_mb: Optional[float] = None
    avg_power_w: Optional[float] = None
    cpu_util_pct: float
    gpu_util_pct: Optional[float] = None
    npu_util_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    memory_efficiency: float  # model_size / peak_ram
    tokens_per_watt: Optional[float] = None

class NormalizationData(BaseModel):
    precision_adjustment: float
    batch_adjustment: float
    prompt_length_adjustment: float
    normalized_tokens_per_sec: float

class ComparatorResult(BaseModel):
    baseline_source: str
    baseline_tokens_per_sec: Optional[float] = None
    delta_pct: float
    delta_abs: float
    probable_causes: List[str] = Field(default_factory=list)
    grade: str  # A, B, C, D, F

class BenchmarkReport(BaseModel):
    run_id: str
    timestamp: datetime
    device: DeviceInfo
    model: ModelConfig
    metrics: BenchmarkMetrics
    normalization: NormalizationData
    comparator: ComparatorResult
    environment_snapshot: Dict[str, Any] = Field(default_factory=dict)
    notes: str = ""

class TelemetrySample(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    gpu_percent: Optional[float] = None
    gpu_vram_used_mb: Optional[float] = None
    npu_percent: Optional[float] = None
    temperature_c: Optional[float] = None
    power_w: Optional[float] = None
    process_name: Optional[str] = None
    process_id: Optional[int] = None

class SystemStatus(BaseModel):
    is_monitoring: bool
    last_sample: Optional[TelemetrySample] = None
    uptime_seconds: float
    samples_collected: int
    alerts: List[str] = Field(default_factory=list)

class ModelRecommendation(BaseModel):
    ai_model_id: str      # Changed from model_id
    ai_model_name: str    # Changed from model_name
    confidence: float
    reason: str
    estimated_tokens_per_sec: float
    estimated_vram_gb: float
    compatible: bool
