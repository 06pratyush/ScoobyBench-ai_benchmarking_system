# API Documentation

## Base URL
```
http://127.0.0.1:8472
```

## Authentication
No authentication required for local use.

## Endpoints

### Health Check
```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "telemetry_running": true
}
```

### System Profile
```
GET /api/system/profile
```

**Response:**
```json
{
  "os": "Windows 11",
  "os_build": "22631",
  "cpu": {
    "name": "Intel Core i7-13700K",
    "vendor": "GenuineIntel",
    "cores": 16,
    "threads": 24,
    "features": ["AVX2", "FMA"]
  },
  "gpus": [
    {
      "name": "NVIDIA GeForce RTX 4090",
      "vendor": "NVIDIA",
      "vram_gb": 24.0,
      "driver": "551.23"
    }
  ],
  "npu": null,
  "ram": {
    "total_gb": 32.0,
    "available_gb": 24.5
  },
  "power_plan": "High performance",
  "bios": {
    "version": "1.2.3",
    "manufacturer": "American Megatrends"
  }
}
```

### Run Benchmark
```
POST /api/benchmark/run
```

**Request Body:**
```json
{
  "model": {
    "name": "llama2-7b-chat",
    "onnx_path": null,
    "params_million": 7000,
    "precision": "fp16",
    "batch_size": 1,
    "prompt_tokens": 128,
    "target_tokens": 512,
    "repeats": 3
  },
  "device_info": null
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "timestamp": "2026-01-15T10:30:00Z",
  "device": { ... },
  "model": { ... },
  "metrics": {
    "latency": {
      "p50_ms": 12.5,
      "p90_ms": 18.2,
      "p99_ms": 25.1,
      "min_ms": 8.3,
      "max_ms": 32.4
    },
    "tokens_per_sec": 45.2,
    "peak_ram_mb": 8192,
    "peak_vram_mb": 6144,
    "avg_power_w": 285.5,
    "cpu_util_pct": 85.2,
    "gpu_util_pct": 92.1,
    "memory_efficiency": 0.85,
    "tokens_per_watt": 0.16
  },
  "normalization": {
    "precision_adjustment": 1.0,
    "batch_adjustment": 1.0,
    "prompt_length_adjustment": 1.0,
    "normalized_tokens_per_sec": 45.2
  },
  "comparator": {
    "baseline_source": "mlperf_reference",
    "baseline_tokens_per_sec": 45.2,
    "delta_pct": 0.0,
    "delta_abs": 0.0,
    "probable_causes": [],
    "grade": "A"
  },
  "notes": "Performance grade: A\nTokens/sec: 45.20 (baseline: 45.20)"
}
```

### List Benchmark Reports
```
GET /api/benchmark/reports?limit=50&offset=0
```

### Get Report
```
GET /api/benchmark/report/{run_id}
```

### Export Report
```
GET /api/benchmark/export/{run_id}?format=json
```

### Start Telemetry
```
POST /api/telemetry/start
```

### Stop Telemetry
```
POST /api/telemetry/stop
```

### Get Telemetry Samples
```
GET /api/telemetry/samples?hours=1
```

### Get Telemetry Statistics
```
GET /api/telemetry/stats?hours=1
```

### Get Telemetry Status
```
GET /api/telemetry/status
```

**Response:**
```json
{
  "is_monitoring": true,
  "last_sample": {
    "timestamp": "2026-01-15T10:30:00Z",
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "memory_used_mb": 19864,
    "gpu_percent": 78.5,
    "gpu_vram_used_mb": 8192,
    "temperature_c": 65.2,
    "power_w": 185.5
  },
  "uptime_seconds": 3600,
  "samples_collected": 720,
  "alerts": ["High memory usage detected"]
}
```

### List Models
```
GET /api/models
```

### Get Model Recommendations
```
GET /api/models/recommendations
```

### Get Configuration
```
GET /api/config
```

### Update Configuration
```
POST /api/config
```

**Request Body:**
```json
{
  "telemetry_interval": 10.0,
  "auto_start_monitor": true
}
```

## WebSocket

### Real-time Telemetry Stream
```
WS /ws/telemetry
```

**Messages:**

Client -> Server:
```json
{"action": "ping"}
{"action": "get_status"}
```

Server -> Client:
```json
{
  "type": "telemetry",
  "timestamp": "2026-01-15T10:30:00Z",
  "cpu_percent": 45.2,
  "memory_percent": 62.1,
  "memory_used_mb": 19864,
  "gpu_percent": 78.5,
  "gpu_vram_used_mb": 8192,
  "temperature_c": 65.2,
  "power_w": 185.5
}
```

```json
{
  "type": "status",
  "data": {
    "is_monitoring": true,
    "samples_collected": 720,
    "alerts": []
  }
}
```

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error description"
}
```

Common status codes:
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
