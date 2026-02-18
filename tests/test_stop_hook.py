"""Tests for .claude/hooks/stop-hook.py."""

from pathlib import Path
from unittest.mock import patch

import pytest

# We test stop-hook functions by importing them.
# The module has early-exit logic based on LOOP_FLAG, so we need to handle that.

HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"


def _import_stop_hook():
    """Import stop_hook module, patching the early-exit check."""
    # Patch sys.stdin.read to avoid blocking
    with patch("sys.stdin.read", return_value="{}"):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "stop_hook", str(HOOKS_DIR / "stop-hook.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


_cached_module = _import_stop_hook()


@pytest.fixture
def stop_hook():
    """Fixture to provide the stop-hook module."""
    return _cached_module


class TestStopHookLogic:
    """Test core logic of stop-hook.py."""

    def test_should_enforce_exit_policy_no_git(self, stop_hook):
        """Test exit policy enforcement when not in git repo."""
        with patch.object(stop_hook, "is_git_repo", return_value=False):
            with patch.object(stop_hook, "loop_guard_active", return_value=False):
                with patch.object(Path, "exists", return_value=False):
                    assert stop_hook.should_enforce_exit_policy({}) is False

    def test_should_enforce_exit_policy_with_promise(self, stop_hook):
        """Test exit policy enforcement when promise is present."""
        assert (
            stop_hook.should_enforce_exit_policy({"completion_promise": "DONE"}) is True
        )

    def test_should_enforce_exit_policy_on_jira_branch(self, stop_hook):
        """Test exit policy on Jira branch."""
        with patch.object(stop_hook, "is_git_repo", return_value=True):
            with patch.object(
                stop_hook, "get_git_branch", return_value="feature/PROJ-123-test"
            ):
                assert stop_hook.should_enforce_exit_policy({}) is True

    def test_should_enforce_exit_policy_on_main_branch(self, stop_hook):
        """Test exit policy skipped on main branch."""
        with patch.object(stop_hook, "is_git_repo", return_value=True):
            with patch.object(stop_hook, "get_git_branch", return_value="main"):
                with patch.object(stop_hook, "loop_guard_active", return_value=False):
                    with patch.object(Path, "exists", return_value=False):
                        assert stop_hook.should_enforce_exit_policy({}) is False

    def test_get_transcript_text(self, stop_hook, tmp_path):
        """Test transcript extraction."""
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("content")

        # Test direct transcript
        assert stop_hook.get_transcript_text({"transcript": "direct"}, 100) == "direct"

        # Test from file
        assert (
            stop_hook.get_transcript_text(
                {"transcript_path": str(transcript_file)}, 100
            )
            == "content"
        )

    def test_check_ui_scope_no_changes(self, stop_hook):
        """Test UI scope check with no changes."""
        with patch.object(
            stop_hook, "get_git_branch", return_value="feature/ui-update"
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                ok, msg = stop_hook.check_ui_scope()
                assert ok is True
                assert msg == ""

    def test_check_pr_merged_main_branch(self, stop_hook):
        """Test PR merge check on main branch (should pass)."""
        with patch.object(stop_hook, "get_git_branch", return_value="main"):
            ok, msg = stop_hook.check_pr_merged()
            assert ok is True
