"""Tests for .claude/hooks/pre-tool-use.py allowlist validation."""

import json
import os
from pathlib import Path
import importlib.util

import pytest

HOOK_PATH = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "pre-tool-use.py"


def _import_pre_tool_use():
    spec = importlib.util.spec_from_file_location("pre_tool_use", str(HOOK_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def pre_tool_use():
    return _import_pre_tool_use()


def _write_allowlist(root: Path, data: dict) -> None:
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "package-allowlist.json").write_text(json.dumps(data))


def test_pinned_npm_version_required(pre_tool_use, tmp_path, monkeypatch):
    allowlist = {
        "policy": {"require_pinned_versions": True},
        "npm": {"jest": ["30.2.0"]},
        "pip": {},
    }
    _write_allowlist(tmp_path, allowlist)
    monkeypatch.chdir(tmp_path)

    allowed, _ = pre_tool_use.validate_package_install("npm install jest@30.2.0")
    assert allowed is True

    allowed, reason = pre_tool_use.validate_package_install("npm install jest")
    assert allowed is False
    assert "pinned version" in reason


def test_pinned_pip_version_required(pre_tool_use, tmp_path, monkeypatch):
    allowlist = {
        "policy": {"require_pinned_versions": True},
        "npm": {},
        "pip": {"pytest": ["*"]},
    }
    _write_allowlist(tmp_path, allowlist)
    monkeypatch.chdir(tmp_path)

    allowed, _ = pre_tool_use.validate_package_install("pip install pytest==8.0.0")
    assert allowed is True

    allowed, reason = pre_tool_use.validate_package_install("pip install pytest>=8.0.0")
    assert allowed is False
    assert "pinned version" in reason


def test_wildcard_scoped_package(pre_tool_use, tmp_path, monkeypatch):
    allowlist = {
        "policy": {"require_pinned_versions": True},
        "npm": {"@types/*": ["*"]},
        "pip": {},
    }
    _write_allowlist(tmp_path, allowlist)
    monkeypatch.chdir(tmp_path)

    allowed, _ = pre_tool_use.validate_package_install("npm install @types/node@20.11.0")
    assert allowed is True
