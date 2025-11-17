"""
Tests for the CLI module.
"""

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from prompt_guard.cli import PromptGuardCLI


class TestCLI:
    """Test suite for the CLI interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = PromptGuardCLI()

    def test_detect_command(self, capsys):
        """Test detect command."""
        result = self.cli.run(
            ["detect", "Contact John at john@example.com", "--policy", "default_pii"]
        )

        assert result == 0
        captured = capsys.readouterr()
        assert "PII Detected" in captured.out
        assert "john@example.com" in captured.out or "[EMAIL_1]" in captured.out

    def test_detect_command_json(self, capsys):
        """Test detect command with JSON output."""
        result = self.cli.run(
            [
                "detect",
                "Contact John at john@example.com",
                "--policy",
                "default_pii",
                "--json",
            ]
        )

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "pii_detected" in data
        assert data["pii_detected"] > 0
        assert "entities" in data

    def test_detect_no_pii(self, capsys):
        """Test detect command with no PII."""
        result = self.cli.run(
            ["detect", "Hello world", "--policy", "default_pii"]
        )

        assert result == 0
        captured = capsys.readouterr()
        assert "No PII detected" in captured.out

    def test_anonymize_command(self, capsys):
        """Test anonymize command."""
        result = self.cli.run(
            ["anonymize", "Email: test@example.com", "--policy", "default_pii"]
        )

        assert result == 0
        captured = capsys.readouterr()
        assert "Anonymized Text" in captured.out
        assert "[EMAIL_" in captured.out

    def test_anonymize_with_save_mapping(self, capsys):
        """Test anonymize command with save mapping."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            mapping_file = f.name

        try:
            result = self.cli.run(
                [
                    "anonymize",
                    "Email: test@example.com",
                    "--policy",
                    "default_pii",
                    "--save-mapping",
                    mapping_file,
                ]
            )

            assert result == 0
            assert Path(mapping_file).exists()

            with open(mapping_file, "r") as f:
                mapping = json.load(f)

            assert len(mapping) > 0
            assert any("EMAIL" in key for key in mapping.keys())

        finally:
            Path(mapping_file).unlink(missing_ok=True)

    def test_deanonymize_command(self, capsys):
        """Test deanonymize command."""
        mapping = {"[EMAIL_1]": "test@example.com", "[NAME_1]": "John"}

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as f:
            json.dump(mapping, f)
            mapping_file = f.name

        try:
            result = self.cli.run(
                [
                    "deanonymize",
                    "Contact [NAME_1] at [EMAIL_1]",
                    "--mapping",
                    mapping_file,
                ]
            )

            assert result == 0
            captured = capsys.readouterr()
            assert "test@example.com" in captured.out
            assert "John" in captured.out

        finally:
            Path(mapping_file).unlink(missing_ok=True)

    def test_scan_command(self, capsys):
        """Test scan command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file1 = Path(tmpdir) / "file1.txt"
            test_file1.write_text("Email: alice@example.com")

            test_file2 = Path(tmpdir) / "file2.txt"
            test_file2.write_text("Phone: 555-1234")

            result = self.cli.run(
                [
                    "scan",
                    str(test_file1),
                    str(test_file2),
                    "--policy",
                    "default_pii",
                ]
            )

            assert result == 0
            captured = capsys.readouterr()
            assert "Scan Results" in captured.out
            assert "Files scanned: 2" in captured.out

    def test_scan_directory(self, capsys):
        """Test scan command on directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "data.txt"
            test_file.write_text("SSN: 123-45-6789")

            result = self.cli.run(
                [
                    "scan",
                    tmpdir,
                    "--policy",
                    "default_pii",
                    "--pattern",
                    "*.txt",
                ]
            )

            assert result == 0
            captured = capsys.readouterr()
            assert "Scan Results" in captured.out

    def test_list_policies(self, capsys):
        """Test list-policies command."""
        result = self.cli.run(["list-policies"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Available Policies" in captured.out
        assert "default_pii" in captured.out

    def test_list_detectors(self, capsys):
        """Test list-detectors command."""
        result = self.cli.run(["list-detectors"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Available Detectors" in captured.out
        assert "regex" in captured.out

    def test_validate_policy(self, capsys):
        """Test validate-policy command."""
        policy_content = """
entities:
  - type: EMAIL
    action: anonymize
  - type: PHONE
    action: anonymize
        """

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".yaml"
        ) as f:
            f.write(policy_content)
            policy_file = f.name

        try:
            result = self.cli.run(["validate-policy", policy_file])

            assert result == 0
            captured = capsys.readouterr()
            assert "Policy file is valid" in captured.out

        finally:
            Path(policy_file).unlink(missing_ok=True)

    def test_validate_invalid_policy(self, capsys):
        """Test validate-policy command with invalid policy."""
        policy_content = """
invalid: structure
        """

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".yaml"
        ) as f:
            f.write(policy_content)
            policy_file = f.name

        try:
            result = self.cli.run(["validate-policy", policy_file])

            assert result == 1
            captured = capsys.readouterr()
            assert "validation failed" in captured.out

        finally:
            Path(policy_file).unlink(missing_ok=True)

    def test_benchmark_command(self, capsys):
        """Test benchmark command."""
        result = self.cli.run(
            ["benchmark", "--detector", "regex", "--iterations", "10"]
        )

        assert result == 0
        captured = capsys.readouterr()
        assert "Benchmark Results" in captured.out
        assert "Average latency" in captured.out
        assert "Throughput" in captured.out

    def test_no_command(self, capsys):
        """Test running with no command."""
        result = self.cli.run([])

        assert result == 1

    def test_version(self, capsys):
        """Test version flag."""
        with pytest.raises(SystemExit) as exc_info:
            self.cli.run(["--version"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Prompt Guard" in captured.out

    def test_help(self, capsys):
        """Test help flag."""
        with pytest.raises(SystemExit) as exc_info:
            self.cli.run(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Prompt Guard - PII Detection" in captured.out
        assert "Examples:" in captured.out
