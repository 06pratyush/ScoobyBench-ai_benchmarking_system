import pytest

from app.utils import validators


class TestRunIdValidation:
    def test_uuid_is_valid(self):
        assert validators.is_valid_run_id("d1f0a2b3-4c5d-6e7f-8a9b-0c1d2e3f4a5b")

    def test_ollama_style_id_is_valid(self):
        assert validators.is_valid_run_id("ollama-1721558400-a1b2c3d4")

    def test_path_traversal_is_rejected(self):
        assert not validators.is_valid_run_id("../../etc/passwd")
        assert not validators.is_valid_run_id("..\\..\\windows\\system32")
        assert not validators.is_valid_run_id("a/b")

    def test_empty_and_oversized_rejected(self):
        assert not validators.is_valid_run_id("")
        assert not validators.is_valid_run_id("x" * 200)

    def test_leading_dot_rejected(self):
        assert not validators.is_valid_run_id(".hidden")


class TestExportFormat:
    def test_supported_formats(self):
        for fmt in ("json", "html", "csv", " JSON ", "Csv"):
            assert validators.validate_export_format(fmt) in validators.SUPPORTED_EXPORT_FORMATS

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError):
            validators.validate_export_format("pdf")
        with pytest.raises(ValueError):
            validators.validate_export_format("")


class TestSanitizeFilename:
    def test_strips_unsafe_characters(self):
        assert validators.sanitize_filename('a<b>:c"|?*') == "a_b_c"

    def test_empty_falls_back_to_default(self):
        assert validators.sanitize_filename("///") == "report"


class TestConfigValidation:
    def test_accepts_known_keys_with_coercion(self):
        result = validators.validate_config_updates({
            "telemetry_interval": "2.5",
            "default_repeats": 5,
            "upload_enabled": "true",
        })
        assert result == {
            "telemetry_interval": 2.5,
            "default_repeats": 5,
            "upload_enabled": True,
        }

    def test_ignores_unknown_and_readonly_keys(self):
        result = validators.validate_config_updates({
            "port": 9999,
            "data_dir": "C:/evil",
            "anonymize": False,
        })
        assert result == {"anonymize": False}

    def test_rejects_uncoercible_value(self):
        with pytest.raises(ValueError):
            validators.validate_config_updates({"default_repeats": "many"})

    def test_rejects_out_of_bounds(self):
        with pytest.raises(ValueError):
            validators.validate_config_updates({"telemetry_interval": 0.01})
        with pytest.raises(ValueError):
            validators.validate_config_updates({"default_repeats": 100})
