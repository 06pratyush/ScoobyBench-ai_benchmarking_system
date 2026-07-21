from app.services import report_generator

SAMPLE_REPORT = {
    "run_id": "test-run-1",
    "timestamp": "2026-07-21T10:00:00+00:00",
    "device": {
        "os": "Windows 11", "cpu": "Test CPU", "cpu_cores": 8, "cpu_threads": 16,
        "gpu": None, "ram_gb": 16.0, "power_plan": "Balanced",
    },
    "model": {
        "name": "phi-2", "precision": "fp16", "batch_size": 1, "repeats": 3,
    },
    "metrics": {
        "tokens_per_sec": 42.5,
        "latency": {"p50_ms": 10.0, "p90_ms": 20.0, "p99_ms": 30.0},
        "peak_ram_mb": 2048.0, "peak_vram_mb": None, "avg_power_w": None,
        "cpu_util_pct": 55.0, "gpu_util_pct": None,
    },
    "comparator": {
        "baseline_source": "generic_cpu", "baseline_tokens_per_sec": 50.0,
        "delta_pct": -15.0, "grade": "B",
        "probable_causes": ["Power plan is 'Balanced'"],
    },
}


class TestHtmlGeneration:
    def test_contains_key_values(self):
        html = report_generator.generate_html(SAMPLE_REPORT)
        assert "phi-2" in html
        assert "42.50" in html
        assert "test-run-1" in html
        assert "Balanced" in html
        assert html.startswith("<!DOCTYPE html>")

    def test_escapes_html_in_fields(self):
        malicious = dict(SAMPLE_REPORT)
        malicious["model"] = {"name": "<script>alert(1)</script>"}
        html = report_generator.generate_html(malicious)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_handles_missing_sections(self):
        html = report_generator.generate_html({"run_id": "sparse"})
        assert "sparse" in html
        assert "—" in html  # placeholder for missing metrics


class TestCsvGeneration:
    def test_header_and_row(self):
        csv_text = report_generator.generate_csv([SAMPLE_REPORT])
        lines = csv_text.strip().split("\n")
        assert len(lines) == 2
        header = lines[0].split(",")
        row = lines[1].split(",")
        assert "tokens_per_sec" in header
        assert "42.5" in row
        assert "B" in row

    def test_multiple_reports(self):
        csv_text = report_generator.generate_csv([SAMPLE_REPORT, SAMPLE_REPORT])
        assert len(csv_text.strip().split("\n")) == 3

    def test_empty_history(self):
        csv_text = report_generator.generate_csv([])
        assert len(csv_text.strip().split("\n")) == 1  # header only
