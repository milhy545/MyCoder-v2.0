"""
Unit tests for CommandParser (v2.1.1)

Tests parsing of CLI commands like /bash, /file, /git into structured Command objects.
"""

import pytest

from mycoder.command_parser import Command, CommandParser, parse_command


class TestCommandParser:
    """Test suite for CommandParser"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = CommandParser()

    def test_parse_bash_command(self):
        """Test parsing /bash command"""
        result = self.parser.parse("/bash ls -la")

        assert result is not None
        assert isinstance(result, Command)
        assert result.tool == "terminal_exec"
        assert result.args == {"command": "ls -la"}
        assert result.raw_input == "/bash ls -la"

    def test_parse_bash_alias_sh(self):
        """Test parsing /sh alias"""
        result = self.parser.parse("/sh pwd")

        assert result is not None
        assert result.tool == "terminal_exec"
        assert result.args == {"command": "pwd"}

    def test_parse_bash_alias_exec(self):
        """Test parsing /exec alias"""
        result = self.parser.parse("/exec echo hello")

        assert result is not None
        assert result.tool == "terminal_exec"
        assert result.args == {"command": "echo hello"}

    def test_parse_file_read(self):
        """Test parsing /file read command"""
        result = self.parser.parse("/file read test.txt")

        assert result is not None
        assert result.tool == "file_read"
        assert result.args == {"path": "test.txt"}

    def test_parse_file_read_shortcut(self):
        """Test parsing /read shortcut"""
        result = self.parser.parse("/read CLAUDE.md")

        assert result is not None
        assert result.tool == "file_read"
        assert result.args == {"path": "CLAUDE.md"}

    def test_parse_file_write(self):
        """Test parsing /file write command"""
        result = self.parser.parse("/file write output.txt")

        assert result is not None
        assert result.tool == "file_write"
        assert result.args == {"path": "output.txt", "content": ""}

    def test_parse_file_write_shortcut(self):
        """Test parsing /write shortcut"""
        result = self.parser.parse("/write test.py")

        assert result is not None
        assert result.tool == "file_write"
        assert result.args == {"path": "test.py", "content": ""}

    def test_parse_file_list(self):
        """Test parsing /file list command"""
        result = self.parser.parse("/file list")

        assert result is not None
        assert result.tool == "file_list"
        assert result.args == {"directory": "."}

    def test_parse_file_list_with_directory(self):
        """Test parsing /file list with directory argument"""
        result = self.parser.parse("/file list src/")

        assert result is not None
        assert result.tool == "file_list"
        assert result.args == {"directory": "src/"}

    def test_parse_file_edit(self):
        """Test parsing /edit command"""
        result = self.parser.parse('/edit foo.txt "old" "new"')

        assert result is not None
        assert result.tool == "file_edit"
        assert result.args == {
            "path": "foo.txt",
            "old_string": "old",
            "new_string": "new",
            "replace_all": False,
        }

    def test_parse_file_edit_replace_all(self):
        """Test parsing /edit with replace all"""
        result = self.parser.parse('/edit foo.txt "old" "new" --all')

        assert result is not None
        assert result.tool == "file_edit"
        assert result.args == {
            "path": "foo.txt",
            "old_string": "old",
            "new_string": "new",
            "replace_all": True,
        }

    def test_parse_git_status(self):
        """Test parsing /git status command"""
        result = self.parser.parse("/git status")

        assert result is not None
        assert result.tool == "git_status"
        assert result.args == {}

    def test_parse_git_diff(self):
        """Test parsing /git diff command"""
        result = self.parser.parse("/git diff")

        assert result is not None
        assert result.tool == "git_diff"
        assert result.args == {}

    def test_parse_git_diff_with_file(self):
        """Test parsing /git diff with file argument"""
        result = self.parser.parse("/git diff main.py")

        assert result is not None
        assert result.tool == "git_diff"
        assert result.args == {"file": "main.py"}

    def test_parse_git_log(self):
        """Test parsing /git log command"""
        result = self.parser.parse("/git log")

        assert result is not None
        assert result.tool == "git_log"
        assert result.args == {}

    def test_parse_git_log_with_options(self):
        """Test parsing /git log with options"""
        result = self.parser.parse("/git log --oneline -5")

        assert result is not None
        assert result.tool == "git_log"
        assert result.args == {"options": "--oneline -5"}

    def test_parse_git_add(self):
        """Test parsing /git add command"""
        result = self.parser.parse("/git add file.txt")

        assert result is not None
        assert result.tool == "git_add"
        assert result.args == {"files": "file.txt"}

    def test_parse_git_commit(self):
        """Test parsing /git commit command"""
        result = self.parser.parse("/git commit Initial commit")

        assert result is not None
        assert result.tool == "git_commit"
        assert result.args == {"message": "Initial commit"}

    def test_parse_git_commit_with_quotes(self):
        """Test parsing /git commit with quoted message"""
        result = self.parser.parse('/git commit "Fix bug in parser"')

        assert result is not None
        assert result.tool == "git_commit"
        assert result.args == {"message": "Fix bug in parser"}

    def test_parse_provider_override(self):
        """Test parsing /provider command"""
        result = self.parser.parse("/provider gemini")

        assert result is not None
        assert result.tool == "provider_override"
        assert result.args == {"provider": "gemini"}

    def test_parse_non_command(self):
        """Test parsing non-command input"""
        result = self.parser.parse("Hello, how are you?")

        assert result is None

    def test_parse_slash_without_command(self):
        """Test parsing slash without valid command"""
        result = self.parser.parse("/unknown")

        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = self.parser.parse("")

        assert result is None

    def test_parse_whitespace_only(self):
        """Test parsing whitespace only"""
        result = self.parser.parse("   ")

        assert result is None

    def test_parse_command_convenience_function(self):
        """Test convenience function parse_command"""
        result = parse_command("/bash echo test")

        assert result is not None
        assert result.tool == "terminal_exec"
        assert result.args == {"command": "echo test"}

    def test_get_help_text(self):
        """Test getting help text"""
        help_text = self.parser.get_help_text()

        assert isinstance(help_text, str)
        assert "/edit" in help_text
        assert "/web" in help_text
        assert "Bash/Terminal" in help_text
        assert "/bash" in help_text
        assert "File Operations" in help_text
        assert "/file read" in help_text
        assert "Git Operations" in help_text
        assert "/git status" in help_text

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive"""
        result_lower = self.parser.parse("/bash ls")
        result_upper = self.parser.parse("/BASH ls")
        result_mixed = self.parser.parse("/BaSh ls")

        assert result_lower is not None
        assert result_upper is not None
        assert result_mixed is not None
        assert result_lower.tool == result_upper.tool == result_mixed.tool
