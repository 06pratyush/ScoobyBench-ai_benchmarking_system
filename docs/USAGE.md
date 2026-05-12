# Usage Guide

## Dashboard

The Dashboard provides an overview of:
- **System Profile**: Your CPU, GPU, RAM, and power plan
- **Quick Actions**: One-click benchmark and monitoring
- **Recommended Models**: AI models compatible with your hardware
- **Recent Benchmarks**: History of past tests

## Running a Benchmark

1. Navigate to **Benchmark** tab
2. Select a model from the dropdown (e.g., Llama-2-7B)
3. Or browse for a custom `.onnx` file
4. Configure:
   - **Precision**: FP32, FP16, INT8, or INT4
   - **Prompt Tokens**: Input sequence length (default: 128)
   - **Target Tokens**: Output length to generate (default: 512)
   - **Repeats**: Number of test runs (default: 3)
5. Click **Start Benchmark**
6. Wait for completion (progress bar shows status)
7. Review results and export JSON report

### Understanding Results

| Metric | Description | Good Value |
|--------|-------------|------------|
| Tokens/sec | Generation speed | Higher is better |
| P50 Latency | Median time per token | Lower is better |
| Peak RAM | Maximum memory used | Should be < 90% of total |
| CPU Util | Processor usage during test | 80-100% is normal |
| Grade | Performance vs baseline | A = Excellent, D = Poor |

### Performance Grades

- **A**: Within 10% of baseline (excellent)
- **B**: Within 25% of baseline (good)
- **C**: Within 50% of baseline (fair)
- **D**: > 50% below baseline (investigate issues)

## System Monitoring

1. Navigate to **System Monitor** tab
2. Click **Start Monitoring**
3. View real-time metrics:
   - CPU usage sparkline
   - Memory consumption
   - GPU utilization (if available)
   - Temperature sensors
4. View historical statistics (1h, 6h, 24h)

### WebSocket Streaming

The monitor uses WebSocket for real-time updates:
- Updates every 5 seconds (configurable)
- Data persists to local SQLite database
- Automatic cleanup after 30 days

## Model Browser

1. Navigate to **Model Browser** tab
2. Browse available AI models
3. Filter by tags or search by name
4. View compatibility indicators:
   - Green checkmark: Compatible with your system
   - Red X: Insufficient resources
5. Click **Benchmark** to test a model
6. Click **HuggingFace** to view model source

### Adding Custom Models

1. Click **Browse** in Benchmark tab
2. Select your `.onnx` file
3. Enter model parameters (size in millions)
4. Run benchmark

## Reports

1. Navigate to **Reports** tab
2. View all benchmark history
3. Click any report for detailed view:
   - Latency distribution (P50/P90/P99)
   - Resource utilization
   - Comparison with baseline
   - Detected issues
4. Click **Export JSON** to save locally

## Settings

Navigate to **Settings** tab to configure:

### Telemetry
- **Sampling Interval**: How often to collect data (1-60 seconds)
- **Data Retention**: How long to keep history (1-365 days)
- **Auto-start**: Begin monitoring on app launch

### Benchmarking
- **Default Repeats**: Number of test iterations
- **Max Duration**: Timeout for long tests

### Privacy
- **Anonymize**: Strip PII from reports
- **Upload**: Allow anonymous data sharing

## CLI Usage (Advanced)

The backend exposes a REST API for automation:

```bash
# Health check
curl http://localhost:8472/api/health

# Get system profile
curl http://localhost:8472/api/system/profile

# Run benchmark
curl -X POST http://localhost:8472/api/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{
    "model": {
      "name": "llama2-7b-chat",
      "params_million": 7000,
      "precision": "fp16",
      "batch_size": 1,
      "prompt_tokens": 128,
      "target_tokens": 512,
      "repeats": 3
    }
  }'

# Get telemetry samples
curl "http://localhost:8472/api/telemetry/samples?hours=1"
```

## Tips for Accurate Benchmarks

1. **Close other applications** - Reduce background CPU/memory usage
2. **Use High Performance power plan** - Prevents CPU throttling
3. **Let system cool** - Avoid thermal throttling
4. **Run multiple times** - Use 3+ repeats for statistical validity
5. **Same conditions** - Keep environment consistent between runs
