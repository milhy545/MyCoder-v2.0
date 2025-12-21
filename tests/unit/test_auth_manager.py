"""Unit tests for AuthManager class.

Tests authentication management, session handling, and configuration validation.
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("claude_cli_auth")
from claude_cli_auth import (
    AuthManager,
    ClaudeAuthError,
    ClaudeConfigError,
    ClaudeSessionError,
)
from claude_cli_auth.models import AuthConfig, SessionStatus


@pytest.mark.unit
class TestAuthManager:
    """Test cases for AuthManager class."""

    def test_init_with_valid_config(self, test_config: AuthConfig):
        """Test AuthManager initialization with valid configuration."""
        with patch("claude_cli_auth.auth_manager.AuthManager._load_sessions"):
            with patch(
                "claude_cli_auth.auth_manager.AuthManager._find_claude_cli"
            ) as mock_find:
                mock_find.return_value = "/usr/local/bin/claude"

                auth_manager = AuthManager(test_config)
                assert auth_manager.config == test_config
                assert isinstance(auth_manager._sessions, dict)

    def test_init_with_invalid_config(self):
        """Test AuthManager initialization with invalid configuration."""
        invalid_config = AuthConfig(
            timeout_seconds=-1,  # Invalid negative timeout
            max_turns=0,  # Invalid zero max turns
        )

        with pytest.raises(ClaudeConfigError) as exc_info:
            AuthManager(invalid_config)

        assert "Configuration validation failed" in str(exc_info.value)
        assert "timeout_seconds must be positive" in str(exc_info.value)

    def test_is_authenticated_success(self, mock_auth_manager: AuthManager):
        """Test successful authentication check."""
        assert mock_auth_manager.is_authenticated() is True

    def test_is_authenticated_no_credentials(self, test_config: AuthConfig):
        """Test authentication check when no credentials file exists."""
        # Remove credentials file
        (test_config.claude_config_dir / ".credentials.json").unlink()

        with patch(
            "claude_cli_auth.auth_manager.AuthManager._find_claude_cli"
        ) as mock_find:
            mock_find.return_value = "/usr/local/bin/claude"

            auth_manager = AuthManager(test_config)
            assert auth_manager.is_authenticated() is False

    def test_is_authenticated_command_failure(self, mock_auth_manager: AuthManager):
        """Test authentication check when command fails."""
        with patch.object(mock_auth_manager, "_run_claude_command") as mock_cmd:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = "Invalid API key"
            mock_result.stderr = "Authentication failed"
            mock_cmd.return_value = mock_result

            assert mock_auth_manager.is_authenticated() is False

    def test_get_authentication_info_success(self, mock_auth_manager: AuthManager):
        """Test getting authentication info successfully."""
        with patch.object(mock_auth_manager, "_run_claude_command") as mock_cmd:
            # Mock version command
            mock_cmd.return_value = MagicMock(returncode=0, stdout="1.0.70")

            info = mock_auth_manager.get_authentication_info()

            assert info["authenticated"] is True
            assert info["claude_cli_version"] == "1.0.70"
            assert info["credentials_file_exists"] is True
            assert info["error"] is None

    def test_get_authentication_info_no_cli(self, mock_auth_manager: AuthManager):
        """Test getting authentication info when CLI not found."""
        with patch.object(mock_auth_manager, "_run_claude_command") as mock_cmd:
            mock_cmd.side_effect = FileNotFoundError("claude not found")

            info = mock_auth_manager.get_authentication_info()

            assert info["authenticated"] is False
            assert "Claude CLI not accessible" in info["error"]

    def test_create_session_success(self, mock_auth_manager: AuthManager):
        """Test successful session creation."""
        session = mock_auth_manager.create_session(
            user_id="test_user",
            working_directory=Path("/tmp/test"),
            session_id="test_session_123",
        )

        assert session.session_id == "test_session_123"
        assert session.user_id == "test_user"
        assert session.working_directory == Path("/tmp/test")
        assert session.status == SessionStatus.ACTIVE

        # Check that session is stored
        assert "test_session_123" in mock_auth_manager._sessions

    def test_create_session_duplicate_id(self, mock_auth_manager: AuthManager):
        """Test creating session with duplicate ID."""
        # Create first session
        mock_auth_manager.create_session(session_id="duplicate_session")

        # Try to create another with same ID
        with pytest.raises(ClaudeSessionError) as exc_info:
            mock_auth_manager.create_session(session_id="duplicate_session")

        assert "Session already exists" in str(exc_info.value)
        assert exc_info.value.session_id == "duplicate_session"

    def test_get_session_exists(self, mock_auth_manager: AuthManager):
        """Test getting existing session."""
        # Create session
        created_session = mock_auth_manager.create_session(session_id="get_test")

        # Get session
        retrieved_session = mock_auth_manager.get_session("get_test")

        assert retrieved_session is not None
        assert retrieved_session.session_id == created_session.session_id

    def test_get_session_not_exists(self, mock_auth_manager: AuthManager):
        """Test getting non-existent session."""
        result = mock_auth_manager.get_session("non_existent_session")
        assert result is None

    def test_get_session_expired(self, mock_auth_manager: AuthManager):
        """Test getting expired session."""
        # Create session and manually expire it
        session = mock_auth_manager.create_session(session_id="expire_test")
        session.last_used = time.time() - (25 * 3600)  # 25 hours ago

        # Configure short timeout for test
        mock_auth_manager.config.session_timeout_hours = 24

        retrieved_session = mock_auth_manager.get_session("expire_test")

        assert retrieved_session is not None
        assert retrieved_session.status == SessionStatus.EXPIRED

    def test_update_session_success(self, mock_auth_manager: AuthManager):
        """Test successful session update."""
        # Create session
        session = mock_auth_manager.create_session(session_id="update_test")
        initial_cost = session.total_cost
        initial_turns = session.total_turns

        # Update session
        result = mock_auth_manager.update_session(
            session_id="update_test", cost=0.05, turns=2, tools_used=3
        )

        assert result is True

        # Check updates
        updated_session = mock_auth_manager.get_session("update_test")
        assert updated_session.total_cost == initial_cost + 0.05
        assert updated_session.total_turns == initial_turns + 2
        assert updated_session.total_tools_used == 3

    def test_update_session_not_exists(self, mock_auth_manager: AuthManager):
        """Test updating non-existent session."""
        result = mock_auth_manager.update_session("non_existent", cost=0.05)
        assert result is False

    def test_update_session_cost_limit_exceeded(self, mock_auth_manager: AuthManager):
        """Test session update exceeding cost limit."""
        # Create session
        session = mock_auth_manager.create_session(session_id="cost_limit_test")

        # Set low cost limit for test
        mock_auth_manager.config.max_cost_per_session = 0.10

        # Update with high cost
        mock_auth_manager.update_session("cost_limit_test", cost=0.15)

        # Check that session is marked as failed
        updated_session = mock_auth_manager.get_session("cost_limit_test")
        assert updated_session.status == SessionStatus.FAILED

    def test_list_sessions_all(self, mock_auth_manager: AuthManager):
        """Test listing all sessions."""
        # Create multiple sessions
        mock_auth_manager.create_session(session_id="session1", user_id="user1")
        mock_auth_manager.create_session(session_id="session2", user_id="user2")
        mock_auth_manager.create_session(session_id="session3", user_id="user1")

        sessions = mock_auth_manager.list_sessions()

        assert len(sessions) == 3
        session_ids = [s.session_id for s in sessions]
        assert "session1" in session_ids
        assert "session2" in session_ids
        assert "session3" in session_ids

    def test_list_sessions_by_user(self, mock_auth_manager: AuthManager):
        """Test listing sessions filtered by user."""
        # Create sessions for different users
        mock_auth_manager.create_session(session_id="user1_session1", user_id="user1")
        mock_auth_manager.create_session(session_id="user1_session2", user_id="user1")
        mock_auth_manager.create_session(session_id="user2_session1", user_id="user2")

        # Get sessions for user1
        user1_sessions = mock_auth_manager.list_sessions(user_id="user1")

        assert len(user1_sessions) == 2
        session_ids = [s.session_id for s in user1_sessions]
        assert "user1_session1" in session_ids
        assert "user1_session2" in session_ids
        assert "user2_session1" not in session_ids

    def test_cleanup_expired_sessions(self, mock_auth_manager: AuthManager):
        """Test cleaning up expired sessions."""
        # Create sessions with different ages
        current_time = time.time()

        # Recent session (not expired)
        recent_session = mock_auth_manager.create_session(session_id="recent")
        recent_session.last_used = current_time - (1 * 3600)  # 1 hour ago

        # Old session (expired)
        old_session = mock_auth_manager.create_session(session_id="old")
        old_session.last_used = current_time - (25 * 3600)  # 25 hours ago

        # Set timeout for test
        mock_auth_manager.config.session_timeout_hours = 24

        # Clean up
        cleaned_count = mock_auth_manager.cleanup_expired_sessions()

        assert cleaned_count == 1
        assert mock_auth_manager.get_session("recent") is not None
        assert mock_auth_manager.get_session("old") is None

    def test_get_usage_summary_single_user(self, mock_auth_manager: AuthManager):
        """Test getting usage summary for single user."""
        # Create sessions with usage data
        session1 = mock_auth_manager.create_session(session_id="s1", user_id="user1")
        session1.total_cost = 0.05
        session1.total_turns = 3
        session1.total_tools_used = 2

        session2 = mock_auth_manager.create_session(session_id="s2", user_id="user1")
        session2.total_cost = 0.03
        session2.total_turns = 2
        session2.total_tools_used = 1

        # Create session for different user
        mock_auth_manager.create_session(session_id="s3", user_id="user2")

        summary = mock_auth_manager.get_usage_summary(user_id="user1")

        assert summary["user_id"] == "user1"
        assert summary["total_sessions"] == 2
        assert summary["total_cost"] == 0.08
        assert summary["total_turns"] == 5
        assert summary["total_tools_used"] == 3
        assert summary["avg_cost_per_session"] == 0.04

    def test_get_usage_summary_all_users(self, mock_auth_manager: AuthManager):
        """Test getting usage summary for all users."""
        # Create sessions for multiple users
        session1 = mock_auth_manager.create_session(session_id="s1", user_id="user1")
        session1.total_cost = 0.05

        session2 = mock_auth_manager.create_session(session_id="s2", user_id="user2")
        session2.total_cost = 0.03

        session3 = mock_auth_manager.create_session(session_id="s3", user_id=None)
        session3.total_cost = 0.02

        summary = mock_auth_manager.get_usage_summary()

        assert summary["user_id"] is None
        assert summary["total_sessions"] == 3
        assert summary["total_cost"] == 0.10

    def test_find_claude_cli_success(self, mock_auth_manager: AuthManager):
        """Test finding Claude CLI executable."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/claude"

            claude_path = mock_auth_manager._find_claude_cli()
            assert claude_path == "/usr/local/bin/claude"

    def test_find_claude_cli_not_found(self, mock_auth_manager: AuthManager):
        """Test Claude CLI not found."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            with patch("glob.glob") as mock_glob:
                mock_glob.return_value = []

                claude_path = mock_auth_manager._find_claude_cli()
                assert claude_path is None

    def test_run_claude_command_success(self, mock_auth_manager: AuthManager):
        """Test successful Claude command execution."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = mock_auth_manager._run_claude_command(["auth", "whoami"])

            assert result.returncode == 0
            assert result.stdout == "success output"

    def test_run_claude_command_timeout(self, mock_auth_manager: AuthManager):
        """Test Claude command timeout."""
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired("claude", 10)

            with pytest.raises(ClaudeAuthError) as exc_info:
                mock_auth_manager._run_claude_command(["auth", "whoami"], timeout=10)

            assert "timed out" in str(exc_info.value)
            assert exc_info.value.error_code == "CLI_TIMEOUT"

    def test_session_persistence(self, mock_auth_manager: AuthManager, temp_dir: Path):
        """Test session persistence to disk."""
        # Create session
        session = mock_auth_manager.create_session(
            session_id="persist_test",
            user_id="test_user",
            working_directory=temp_dir,
        )
        session.total_cost = 0.05
        session.total_turns = 3

        # Force save
        mock_auth_manager._save_sessions()

        # Check that file exists and contains data
        session_file = mock_auth_manager._session_file
        assert session_file.exists()

        with open(session_file, "r") as f:
            data = json.load(f)

        assert "persist_test" in data
        assert data["persist_test"]["user_id"] == "test_user"
        assert data["persist_test"]["total_cost"] == 0.05
        assert data["persist_test"]["total_turns"] == 3

    def test_session_loading(self, test_config: AuthConfig, temp_dir: Path):
        """Test loading sessions from disk."""
        # Create session file manually
        session_file = test_config.claude_config_dir / "claude_cli_auth_sessions.json"
        session_data = {
            "load_test": {
                "session_id": "load_test",
                "user_id": "test_user",
                "working_directory": str(temp_dir),
                "created_at": time.time(),
                "last_used": time.time(),
                "total_cost": 0.08,
                "total_turns": 4,
                "total_tools_used": 2,
                "status": "active",
                "model_info": None,
                "config": {},
            }
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f)

        # Create AuthManager (should load sessions)
        with patch(
            "claude_cli_auth.auth_manager.AuthManager._run_claude_command"
        ) as mock_cmd:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test@example.com"
            mock_cmd.return_value = mock_result

            with patch(
                "claude_cli_auth.auth_manager.AuthManager._find_claude_cli"
            ) as mock_find:
                mock_find.return_value = "/usr/local/bin/claude"

                auth_manager = AuthManager(test_config)

        # Check that session was loaded
        session = auth_manager.get_session("load_test")
        assert session is not None
        assert session.user_id == "test_user"
        assert session.total_cost == 0.08
        assert session.total_turns == 4
