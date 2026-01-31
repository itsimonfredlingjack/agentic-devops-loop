"""Tests for .claude/hooks/stop-hook.py \u2014 verification enforcement.

Tests the functions: detect_project_types(), run_tests(), run_lint(),
and the integration of verification into the promise detection flow.
"""

from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

# We test stop-hook functions by importing them. The module has early-exit
# logic based on LOOP_FLAG, so we need to handle that.
# We'll import specific functions after patching.

HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"

def _import_stop_hook():
    """Import stop_hook module, patching the early-exit check."""
    # Patch Path.exists to return True for LOOP_FLAG during import
    original_exists = Path.exists
    def patched_exists(self):
        if str(self).endswith(".ralph_loop_active"):
            return True
        return original_exists(self)

    with patch.object(Path, "exists", patched_exists):
        # The module is stop-hook.py (with dash), so import via importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "stop_hook", str(HOOKS_DIR / "stop-hook.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


# Cache at module level \u2014 only import once per test session
_cached_module = _import_stop_hook()


@pytest.fixture
def stop_hook():
    """Fixture to provide the stop-hook module."""
    return _cached_module


# ---------------------------------------------------------------------------
# detect_project_types
# ---------------------------------------------------------------------------

class TestDetectProjectType:
    """Test project type detection from config files."""

    def test_detects_node_from_package_json(self, stop_hook, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "test"}')
        assert stop_hook.detect_project_types(tmp_path) == {"node"}

    def test_detects_python_from_pyproject_toml(self, stop_hook, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        assert stop_hook.detect_project_types(tmp_path) == {"python"}

    def test_detects_python_from_setup_py(self, stop_hook, tmp_path):
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        assert stop_hook.detect_project_types(tmp_path) == {"python"}

    def test_returns_unknown_when_no_markers(self, stop_hook, tmp_path):
        assert stop_hook.detect_project_types(tmp_path) == set()

    def test_prefers_node_when_both_exist(self, stop_hook, tmp_path):
        (tmp_path / "package.json").write_text('{}')
        (tmp_path / "pyproject.toml").write_text("")
        assert stop_hook.detect_project_types(tmp_path) == {"node", "python"}


# ---------------------------------------------------------------------------
# run_tests
# ---------------------------------------------------------------------------

class TestRunTests:
    """Test runner execution with timeout and error handling."""

    @patch("subprocess.run")
    def test_node_tests_pass(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "test"], returncode=0, stdout="ok", stderr=""
        )
        passed, output = stop_hook.run_tests("node")
        assert passed is True

    @patch("subprocess.run")
    def test_node_tests_fail(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "test"], returncode=1, stdout="", stderr="FAIL"
        )
        passed, output = stop_hook.run_tests("node")
        assert passed is False
        assert "FAIL" in output

    @patch("subprocess.run")
    def test_python_tests_pass(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest"], returncode=0, stdout="passed", stderr=""
        )
        passed, _ = stop_hook.run_tests("python")
        assert passed is True

    @patch("subprocess.run")
    def test_python_tests_fail(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest"], returncode=1, stdout="", stderr="FAILED"
        )
        passed, output = stop_hook.run_tests("python")
        assert passed is False
        assert "FAILED" in output

    @patch("subprocess.run")
    def test_timeout_returns_false(self, mock_run, stop_hook):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=120)
        passed, output = stop_hook.run_tests("node")
        assert passed is False
        assert "timed out" in output

    @patch("subprocess.run")
    def test_runner_not_found_fails_closed(self, mock_run, stop_hook):
        # Fail-closed: if test runner not found, block exit
        mock_run.side_effect = FileNotFoundError("npm not found")
        passed, output = stop_hook.run_tests("node")
        assert passed is False
        assert "not found" in output

    def test_unknown_project_type_returns_false(self, stop_hook):
        passed, _ = stop_hook.run_tests("unknown")
        assert passed is False


# ---------------------------------------------------------------------------
# run_lint
# ---------------------------------------------------------------------------

class TestRunLint:
    """Lint runner execution with timeout and error handling."""

    @patch("subprocess.run")
    def test_node_lint_pass(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "run", "lint"], returncode=0, stdout="ok", stderr=""
        )
        passed, _ = stop_hook.run_lint("node")
        assert passed is True

    @patch("subprocess.run")
    def test_node_lint_fail(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "run", "lint"], returncode=1, stdout="", stderr="errors"
        )
        passed, output = stop_hook.run_lint("node")
        assert passed is False
        assert "errors" in output

    @patch("subprocess.run")
    def test_python_lint_pass(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["ruff", "check", "."], returncode=0, stdout="ok", stderr=""
        )
        passed, _ = stop_hook.run_lint("python")
        assert passed is True

    @patch("subprocess.run")
    def test_timeout_returns_false(self, mock_run, stop_hook):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="lint", timeout=60)
        passed, output = stop_hook.run_lint("node")
        assert passed is False
        assert "timed out" in output

    @patch("subprocess.run")
    def test_linter_not_found_fails_closed(self, mock_run, stop_hook):
        # Fail-closed: if linter not found, block exit
        mock_run.side_effect = FileNotFoundError("ruff not found")
        passed, output = stop_hook.run_lint("python")
        assert passed is False
        assert "not found" in output

    def test_unknown_project_type_returns_false(self, stop_hook):
        passed, _ = stop_hook.run_lint("unknown")
        assert passed is False


# ---------------------------------------------------------------------------
# Integration: promise + verification flow
# ---------------------------------------------------------------------------

class TestVerifyBeforeExit:
    """Test the verify_before_exit() function that gates promise\u2192exit."""

    @patch("subprocess.run")
    def test_all_pass_returns_true(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        requirements = {"tests_must_pass": True, "lint_must_pass": True}
        passed, detail = stop_hook.verify_before_exit(requirements, {"node"})
        assert passed is True
        assert detail == ""

    @patch("subprocess.run")
    def test_tests_fail_returns_false_with_detail(self, mock_run, stop_hook):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="FAIL test_login", stderr=""
        )
        requirements = {"tests_must_pass": True, "lint_must_pass": False}
        passed, detail = stop_hook.verify_before_exit(requirements, {"node"})
        assert passed is False
        assert "Tests failed" in detail
        assert "FAIL test_login" in detail

    def test_tests_not_required_skips(self, stop_hook):
        requirements = {"tests_must_pass": False, "lint_must_pass": False}
        passed, detail = stop_hook.verify_before_exit(requirements, {"node"})
        assert passed is True

    @patch("subprocess.run")
    def test_lint_fail_returns_false_with_detail(self, mock_run, stop_hook):
        # First call (tests) passes, second call (lint) fails
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout="lint error at line 5", stderr=""),
        ]
        requirements = {"tests_must_pass": True, "lint_must_pass": True}
        passed, detail = stop_hook.verify_before_exit(requirements, {"node"})
        assert passed is False
        assert "Lint failed" in detail
        assert "lint error" in detail
