"""Pytest configuration for ScoobyBench backend tests.

Redirects SCOOBYBENCH_HOME to a temp directory BEFORE any app module is
imported, so tests never touch the real ~/.scoobybench data or database.
"""
import os
import sys
import tempfile
from pathlib import Path

_TEST_HOME = tempfile.mkdtemp(prefix="scoobybench_test_")
os.environ.setdefault("SCOOBYBENCH_HOME", _TEST_HOME)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
