"""Tests for .claude/utils/jira_api.py \u2014 Python Jira API fallback."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the utils directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "utils"))

import jira_api

# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------


class TestLoadCredentials:
    """Test credential loading from .env files."""

    def test_loads_standard_credentials(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "JIRA_URL=https://test.atlassian.net\n"
            "JIRA_USERNAME=user@example.com\n"
            "JIRA_API_TOKEN=tok123\n"
        )
        creds = jira_api.load_credentials(str(env_file))
        assert creds["url"] == "https://test.atlassian.net"
        assert creds["username"] == "user@example.com"
        assert creds["token"] == "tok123"

    def test_loads_alternative_credential_names(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "JIRA_URL=https://alt.atlassian.net\n"
            "JIRA_EMAIL=alt@example.com\n"
            "JIRA_TOKEN=alttoken\n"
        )
        creds = jira_api.load_credentials(str(env_file))
        assert creds["username"] == "alt@example.com"
        assert creds["token"] == "alttoken"

    def test_missing_env_file_raises(self):
        with pytest.raises(FileNotFoundError):
            jira_api.load_credentials("/nonexistent/.env")

    def test_missing_required_fields_raises(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_URL=https://test.atlassian.net\n")
        with pytest.raises(ValueError, match="Missing.*credentials"):
            jira_api.load_credentials(str(env_file))

    def test_strips_surrounding_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            'JIRA_URL="https://quoted.atlassian.net"\n'
            "JIRA_USERNAME='quoted@example.com'\n"
            'JIRA_API_TOKEN="quotedtok"\n'
        )
        creds = jira_api.load_credentials(str(env_file))
        assert creds["url"] == "https://quoted.atlassian.net"
        assert creds["username"] == "quoted@example.com"
        assert creds["token"] == "quotedtok"

    def test_ignores_comments_and_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# Jira credentials\n"
            "\n"
            "JIRA_URL=https://test.atlassian.net\n"
            "JIRA_USERNAME=user@example.com\n"
            "# This is the API token\n"
            "JIRA_API_TOKEN=tok123\n"
        )
        creds = jira_api.load_credentials(str(env_file))
        assert creds["url"] == "https://test.atlassian.net"


# ---------------------------------------------------------------------------
# Auth header
# ---------------------------------------------------------------------------


class TestBuildAuthHeader:
    """Test Basic auth header construction."""

    def test_auth_header_is_base64_encoded(self):
        import base64

        creds = {"url": "https://x.atlassian.net", "username": "u", "token": "t"}
        headers = jira_api.build_headers(creds)
        expected = base64.b64encode(b"u:t").decode()
        assert headers["Authorization"] == f"Basic {expected}"

    def test_headers_include_json_content_type(self):
        creds = {"url": "https://x.atlassian.net", "username": "u", "token": "t"}
        headers = jira_api.build_headers(creds)
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"


# ---------------------------------------------------------------------------
# get-issue
# ---------------------------------------------------------------------------


class TestGetIssue:
    """Test get_issue() makes correct API call."""

    @patch("jira_api.urlopen")
    def test_get_issue_calls_correct_url(self, mock_urlopen):
        response_body = json.dumps(
            {"key": "PROJ-1", "fields": {"summary": "Test issue"}}
        ).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        creds = {"url": "https://test.atlassian.net", "username": "u", "token": "t"}
        result = jira_api.get_issue(creds, "PROJ-1")

        # Verify the URL uses issue/ (singular), not issues/
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "/rest/api/3/issue/PROJ-1" in request.full_url
        assert result["key"] == "PROJ-1"

    @patch("jira_api.urlopen")
    def test_get_issue_handles_http_error(self, mock_urlopen):
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            url="http://x", code=404, msg="Not Found", hdrs=None, fp=None
        )
        creds = {"url": "https://test.atlassian.net", "username": "u", "token": "t"}
        with pytest.raises(jira_api.JiraAPIError, match="404"):
            jira_api.get_issue(creds, "PROJ-999")


# ---------------------------------------------------------------------------
# transition-issue
# ---------------------------------------------------------------------------


class TestTransitionIssue:
    """Test transition_issue() makes correct API calls."""

    @patch("jira_api.urlopen")
    def test_transition_fetches_then_posts(self, mock_urlopen):
        # First call: GET transitions
        transitions_body = json.dumps(
            {
                "transitions": [
                    {"id": "31", "to": {"name": "In Progress"}},
                    {"id": "41", "to": {"name": "Done"}},
                ]
            }
        ).encode()
        # Second call: POST transition
        post_resp_body = b""

        get_resp = MagicMock()
        get_resp.read.return_value = transitions_body
        get_resp.__enter__ = lambda s: s
        get_resp.__exit__ = MagicMock(return_value=False)

        post_resp = MagicMock()
        post_resp.read.return_value = post_resp_body
        post_resp.__enter__ = lambda s: s
        post_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [get_resp, post_resp]

        creds = {"url": "https://test.atlassian.net", "username": "u", "token": "t"}
        jira_api.transition_issue(creds, "PROJ-1", "In Progress")

        assert mock_urlopen.call_count == 2
        # First call: GET transitions \u2014 uses issue/ (singular)
        first_req = mock_urlopen.call_args_list[0][0][0]
        assert "/rest/api/3/issue/PROJ-1/transitions" in first_req.full_url

        # Second call: POST transition
        second_req = mock_urlopen.call_args_list[1][0][0]
        assert second_req.method == "POST"
        body = json.loads(second_req.data)
        assert body["transition"]["id"] == "31"

    @patch("jira_api.urlopen")
    def test_transition_unknown_status_raises(self, mock_urlopen):
        transitions_body = json.dumps(
            {"transitions": [{"id": "31", "to": {"name": "In Progress"}}]}
        ).encode()
        resp = MagicMock()
        resp.read.return_value = transitions_body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        creds = {"url": "https://test.atlassian.net", "username": "u", "token": "t"}
        with pytest.raises(jira_api.JiraAPIError, match="NoSuchStatus"):
            jira_api.transition_issue(creds, "PROJ-1", "NoSuchStatus")


# ---------------------------------------------------------------------------
# add-comment
# ---------------------------------------------------------------------------


class TestAddComment:
    """Test add_comment() makes correct API call with ADF format."""

    @patch("jira_api.urlopen")
    def test_add_comment_posts_adf_body(self, mock_urlopen):
        post_resp = MagicMock()
        post_resp.read.return_value = json.dumps({"id": "10001"}).encode()
        post_resp.__enter__ = lambda s: s
        post_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = post_resp

        creds = {"url": "https://test.atlassian.net", "username": "u", "token": "t"}
        jira_api.add_comment(creds, "PROJ-1", "Hello from tests")

        req = mock_urlopen.call_args[0][0]
        # Uses issue/ (singular), not issues/
        assert "/rest/api/3/issue/PROJ-1/comment" in req.full_url
        assert req.method == "POST"
        body = json.loads(req.data)
        # ADF format check
        assert body["body"]["type"] == "doc"
        assert body["body"]["version"] == 1
        paragraph = body["body"]["content"][0]
        assert paragraph["type"] == "paragraph"
        assert paragraph["content"][0]["text"] == "Hello from tests"


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------


class TestCLI:
    """Test the CLI entrypoint dispatches commands correctly."""

    @patch("jira_api.get_issue")
    @patch("jira_api.find_env_file")
    @patch("jira_api.load_credentials")
    def test_cli_get_issue(self, mock_load, mock_find, mock_get):
        mock_find.return_value = "/tmp/.env"
        mock_load.return_value = {"url": "https://x", "username": "u", "token": "t"}
        mock_get.return_value = {"key": "PROJ-1"}

        result = jira_api.cli(["get-issue", "PROJ-1"])
        mock_get.assert_called_once()
        assert result == 0

    def test_cli_unknown_command(self):
        result = jira_api.cli(["unknown-cmd"])
        assert result != 0
