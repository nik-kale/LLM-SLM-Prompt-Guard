"""
Tests for the CLI and detection reports.
"""

import json
import os
import stat
import sys

import pytest
from click.testing import CliRunner

from prompt_guard import PromptGuard
from prompt_guard.cli import cli
from prompt_guard.report import generate_detection_report
from prompt_guard.types import DetectorResult, RiskLevel


class TestDetectionReport:
    def test_overlapping_detections_are_counted_once(self):
        # RegexDetector reports an SSN as both SSN and PHONE; the old sum of
        # span lengths reported 200% coverage for this text.
        report = PromptGuard().detect_only("123-45-6789")

        assert report.summary == {"PHONE": 1, "SSN": 1}
        assert report.pii_chars == 11
        assert report.coverage == 1.0

    @pytest.mark.parametrize("entity_type", ["DRIVERS_LICENSE", "MRN", "EIN", "NIN_UK"])
    def test_detector_entity_names_count_as_high_risk(self, entity_type):
        entity = DetectorResult(entity_type, 0, 8, "X1234567")

        report = generate_detection_report("X1234567 and some more text", [entity])

        assert report.risk_score == RiskLevel.CRITICAL


class TestCli:
    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
    def test_files_with_original_values_are_private(self, tmp_path):
        mapping_file = tmp_path / "mapping.json"
        anonymized_file = tmp_path / "anon.txt"
        restored_file = tmp_path / "restored.txt"
        restored_file.write_text("stale")
        os.chmod(restored_file, 0o640)
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "anonymize",
                "Mail john@example.com",
                "--output",
                str(anonymized_file),
                "--mapping-output",
                str(mapping_file),
            ],
        )
        assert result.exit_code == 0, result.output
        result = runner.invoke(
            cli,
            [
                "deanonymize",
                "--file",
                str(anonymized_file),
                "--mapping",
                str(mapping_file),
                "--output",
                str(restored_file),
            ],
        )
        assert result.exit_code == 0, result.output

        assert json.loads(mapping_file.read_text()) == {"[EMAIL_1]": "john@example.com"}
        assert restored_file.read_text() == "Mail john@example.com"
        assert stat.S_IMODE(mapping_file.stat().st_mode) == 0o600
        assert stat.S_IMODE(restored_file.stat().st_mode) == 0o600

    @pytest.mark.parametrize("command", ["list-policies", "list-detectors"])
    def test_documented_command_names(self, command):
        result = CliRunner().invoke(cli, [command])

        assert result.exit_code == 0, result.output
