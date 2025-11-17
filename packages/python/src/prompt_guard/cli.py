"""
Command Line Interface for Prompt Guard.

This module provides a comprehensive CLI for PII detection, anonymization,
file scanning, and interactive analysis.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

from prompt_guard import PromptGuard, __version__, list_detectors, list_policies


class PromptGuardCLI:
    """Command-line interface for Prompt Guard."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._create_parser()
        self.guard: Optional[PromptGuard] = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all commands."""
        parser = argparse.ArgumentParser(
            prog="prompt-guard",
            description="Prompt Guard - PII Detection and Anonymization CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Quick PII detection
  prompt-guard detect "John's email is john@example.com"

  # Scan files
  prompt-guard scan data/*.txt --policy hipaa_phi

  # Interactive mode
  prompt-guard interactive

  # List available policies
  prompt-guard list-policies

  # List available detectors
  prompt-guard list-detectors

  # Anonymize and save mapping
  prompt-guard anonymize "Contact John at 555-1234" --save-mapping mapping.json

  # De-anonymize using mapping
  prompt-guard deanonymize "Contact [NAME_1] at [PHONE_1]" --mapping mapping.json
            """,
        )

        parser.add_argument(
            "--version", action="version", version=f"Prompt Guard v{__version__}"
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # detect command
        detect_parser = subparsers.add_parser(
            "detect", help="Detect PII in text without anonymization"
        )
        detect_parser.add_argument("text", help="Text to analyze for PII")
        detect_parser.add_argument(
            "--policy",
            "-p",
            default="default_pii",
            help="Policy to use (default: default_pii)",
        )
        detect_parser.add_argument(
            "--detector",
            "-d",
            default="regex",
            help="Detector to use (default: regex)",
        )
        detect_parser.add_argument(
            "--json", action="store_true", help="Output results as JSON"
        )
        detect_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Show detailed detection info"
        )

        # scan command
        scan_parser = subparsers.add_parser(
            "scan", help="Scan files or directories for PII"
        )
        scan_parser.add_argument(
            "paths", nargs="+", help="Files or directories to scan"
        )
        scan_parser.add_argument(
            "--policy",
            "-p",
            default="default_pii",
            help="Policy to use (default: default_pii)",
        )
        scan_parser.add_argument(
            "--detector",
            "-d",
            default="regex",
            help="Detector to use (default: regex)",
        )
        scan_parser.add_argument(
            "--recursive", "-r", action="store_true", help="Scan directories recursively"
        )
        scan_parser.add_argument(
            "--pattern",
            default="*.txt,*.md,*.json,*.log",
            help="File patterns to scan (comma-separated, default: *.txt,*.md,*.json,*.log)",
        )
        scan_parser.add_argument(
            "--json", action="store_true", help="Output results as JSON"
        )
        scan_parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Show only summary, not individual detections",
        )

        # anonymize command
        anon_parser = subparsers.add_parser(
            "anonymize", help="Anonymize PII in text"
        )
        anon_parser.add_argument("text", help="Text to anonymize")
        anon_parser.add_argument(
            "--policy",
            "-p",
            default="default_pii",
            help="Policy to use (default: default_pii)",
        )
        anon_parser.add_argument(
            "--detector",
            "-d",
            default="regex",
            help="Detector to use (default: regex)",
        )
        anon_parser.add_argument(
            "--save-mapping",
            "-s",
            metavar="FILE",
            help="Save mapping table to file (JSON format)",
        )
        anon_parser.add_argument(
            "--json", action="store_true", help="Output results as JSON"
        )

        # deanonymize command
        deanon_parser = subparsers.add_parser(
            "deanonymize", help="Restore original text from anonymized version"
        )
        deanon_parser.add_argument("text", help="Anonymized text to restore")
        deanon_parser.add_argument(
            "--mapping",
            "-m",
            required=True,
            metavar="FILE",
            help="Mapping file (JSON format)",
        )
        deanon_parser.add_argument(
            "--json", action="store_true", help="Output results as JSON"
        )

        # interactive command
        interactive_parser = subparsers.add_parser(
            "interactive", help="Start interactive PII analysis mode"
        )
        interactive_parser.add_argument(
            "--policy",
            "-p",
            default="default_pii",
            help="Policy to use (default: default_pii)",
        )
        interactive_parser.add_argument(
            "--detector",
            "-d",
            default="regex",
            help="Detector to use (default: regex)",
        )

        # list-policies command
        subparsers.add_parser("list-policies", help="List all available policies")

        # list-detectors command
        subparsers.add_parser("list-detectors", help="List all available detectors")

        # validate-policy command
        validate_parser = subparsers.add_parser(
            "validate-policy", help="Validate a policy file"
        )
        validate_parser.add_argument("policy_file", help="Path to policy YAML file")

        # benchmark command
        benchmark_parser = subparsers.add_parser(
            "benchmark", help="Benchmark detector performance"
        )
        benchmark_parser.add_argument(
            "--detector",
            "-d",
            help="Specific detector to benchmark (default: all available)",
        )
        benchmark_parser.add_argument(
            "--iterations",
            "-i",
            type=int,
            default=1000,
            help="Number of iterations (default: 1000)",
        )

        return parser

    def _initialize_guard(self, policy: str, detector: str) -> None:
        """Initialize PromptGuard with specified policy and detector."""
        try:
            self.guard = PromptGuard(policy=policy, detectors=[detector])
        except Exception as e:
            self._error(f"Failed to initialize Prompt Guard: {e}")
            sys.exit(1)

    def _error(self, message: str) -> None:
        """Print error message to stderr."""
        print(f"Error: {message}", file=sys.stderr)

    def _success(self, message: str) -> None:
        """Print success message to stdout."""
        print(f"✓ {message}")

    def _info(self, message: str) -> None:
        """Print info message to stdout."""
        print(f"ℹ {message}")

    def cmd_detect(self, args: argparse.Namespace) -> int:
        """Execute detect command."""
        self._initialize_guard(args.policy, args.detector)

        # Perform anonymization to detect PII
        anonymized, mapping = self.guard.anonymize(args.text)

        if args.json:
            result = {
                "original": args.text,
                "anonymized": anonymized,
                "pii_detected": len(mapping),
                "entities": mapping,
                "policy": args.policy,
                "detector": args.detector,
            }
            print(json.dumps(result, indent=2))
        else:
            if mapping:
                print(f"\n🔍 PII Detected ({len(mapping)} entities):\n")
                print(f"Original:    {args.text}")
                print(f"Anonymized:  {anonymized}\n")

                if args.verbose:
                    print("Detected Entities:")
                    for placeholder, original in mapping.items():
                        entity_type = placeholder.split("_")[0].strip("[]")
                        print(f"  • {entity_type}: {original} → {placeholder}")
                else:
                    entity_types = {}
                    for placeholder in mapping.keys():
                        entity_type = placeholder.split("_")[0].strip("[]")
                        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

                    print("Entity Summary:")
                    for entity_type, count in sorted(entity_types.items()):
                        print(f"  • {entity_type}: {count}")
            else:
                self._success("No PII detected in the provided text.")

        return 0

    def cmd_scan(self, args: argparse.Namespace) -> int:
        """Execute scan command."""
        self._initialize_guard(args.policy, args.detector)

        patterns = args.pattern.split(",")
        files_to_scan: List[Path] = []

        # Collect files to scan
        for path_str in args.paths:
            path = Path(path_str)
            if path.is_file():
                files_to_scan.append(path)
            elif path.is_dir():
                if args.recursive:
                    for pattern in patterns:
                        files_to_scan.extend(path.rglob(pattern.strip()))
                else:
                    for pattern in patterns:
                        files_to_scan.extend(path.glob(pattern.strip()))
            else:
                self._error(f"Path not found: {path_str}")

        if not files_to_scan:
            self._error("No files found to scan")
            return 1

        # Scan files
        results: Dict[str, Tuple[str, Dict]] = {}
        total_pii = 0

        for file_path in files_to_scan:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                anonymized, mapping = self.guard.anonymize(content)
                results[str(file_path)] = (anonymized, mapping)
                total_pii += len(mapping)
            except Exception as e:
                self._error(f"Failed to scan {file_path}: {e}")

        # Output results
        if args.json:
            output = {
                "summary": {
                    "files_scanned": len(files_to_scan),
                    "files_with_pii": sum(1 for _, m in results.values() if m),
                    "total_pii_found": total_pii,
                    "policy": args.policy,
                    "detector": args.detector,
                },
                "files": {
                    path: {"pii_count": len(mapping), "entities": mapping}
                    for path, (_, mapping) in results.items()
                },
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\n📂 Scan Results:\n")
            print(f"Files scanned: {len(files_to_scan)}")
            print(f"Files with PII: {sum(1 for _, m in results.values() if m)}")
            print(f"Total PII found: {total_pii}\n")

            if not args.summary_only:
                for file_path, (anonymized, mapping) in results.items():
                    if mapping:
                        print(f"\n📄 {file_path}:")
                        print(f"   PII entities: {len(mapping)}")

                        entity_types = {}
                        for placeholder in mapping.keys():
                            entity_type = placeholder.split("_")[0].strip("[]")
                            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

                        for entity_type, count in sorted(entity_types.items()):
                            print(f"   • {entity_type}: {count}")

        return 0

    def cmd_anonymize(self, args: argparse.Namespace) -> int:
        """Execute anonymize command."""
        self._initialize_guard(args.policy, args.detector)

        anonymized, mapping = self.guard.anonymize(args.text)

        # Save mapping if requested
        if args.save_mapping:
            try:
                with open(args.save_mapping, "w", encoding="utf-8") as f:
                    json.dump(mapping, f, indent=2, ensure_ascii=False)
                self._success(f"Mapping saved to {args.save_mapping}")
            except Exception as e:
                self._error(f"Failed to save mapping: {e}")
                return 1

        if args.json:
            result = {
                "original": args.text,
                "anonymized": anonymized,
                "mapping": mapping,
                "policy": args.policy,
                "detector": args.detector,
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"\n🔒 Anonymized Text:\n")
            print(anonymized)
            if mapping:
                print(f"\n📋 Mapping Table ({len(mapping)} entities):")
                for placeholder, original in mapping.items():
                    print(f"  {placeholder} → {original}")

        return 0

    def cmd_deanonymize(self, args: argparse.Namespace) -> int:
        """Execute deanonymize command."""
        # Load mapping
        try:
            with open(args.mapping, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except Exception as e:
            self._error(f"Failed to load mapping file: {e}")
            return 1

        # De-anonymize
        deanonymized = args.text
        for placeholder, original in mapping.items():
            deanonymized = deanonymized.replace(placeholder, original)

        if args.json:
            result = {
                "anonymized": args.text,
                "deanonymized": deanonymized,
                "mapping": mapping,
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"\n🔓 De-anonymized Text:\n")
            print(deanonymized)

        return 0

    def cmd_interactive(self, args: argparse.Namespace) -> int:
        """Execute interactive command."""
        self._initialize_guard(args.policy, args.detector)

        print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Prompt Guard - Interactive PII Analysis              ║
╚══════════════════════════════════════════════════════════════╝

Policy:   {args.policy}
Detector: {args.detector}

Commands:
  • Enter text to analyze for PII
  • 'help' - Show this help message
  • 'policy <name>' - Switch to a different policy
  • 'detector <name>' - Switch to a different detector
  • 'list-policies' - Show available policies
  • 'list-detectors' - Show available detectors
  • 'quit' or 'exit' - Exit interactive mode

Press Ctrl+C or Ctrl+D to exit at any time.
        """)

        while True:
            try:
                # Read input
                text = input("\n> ").strip()

                if not text:
                    continue

                # Handle commands
                if text.lower() in ("quit", "exit"):
                    break
                elif text.lower() == "help":
                    print("""
Commands:
  • Enter text to analyze for PII
  • 'policy <name>' - Switch to a different policy
  • 'detector <name>' - Switch to a different detector
  • 'list-policies' - Show available policies
  • 'list-detectors' - Show available detectors
  • 'quit' or 'exit' - Exit interactive mode
                    """)
                elif text.lower().startswith("policy "):
                    new_policy = text[7:].strip()
                    try:
                        self._initialize_guard(new_policy, args.detector)
                        args.policy = new_policy
                        self._success(f"Switched to policy: {new_policy}")
                    except Exception as e:
                        self._error(f"Failed to switch policy: {e}")
                elif text.lower().startswith("detector "):
                    new_detector = text[9:].strip()
                    try:
                        self._initialize_guard(args.policy, new_detector)
                        args.detector = new_detector
                        self._success(f"Switched to detector: {new_detector}")
                    except Exception as e:
                        self._error(f"Failed to switch detector: {e}")
                elif text.lower() == "list-policies":
                    policies = list_policies()
                    print("\nAvailable policies:")
                    for policy in policies:
                        marker = "✓" if policy == args.policy else " "
                        print(f"  [{marker}] {policy}")
                elif text.lower() == "list-detectors":
                    detectors = list_detectors()
                    print("\nAvailable detectors:")
                    for detector in detectors:
                        marker = "✓" if detector == args.detector else " "
                        print(f"  [{marker}] {detector}")
                else:
                    # Analyze text
                    anonymized, mapping = self.guard.anonymize(text)

                    if mapping:
                        print(f"\n🔍 PII Detected ({len(mapping)} entities):")
                        print(f"\nOriginal:    {text}")
                        print(f"Anonymized:  {anonymized}\n")

                        entity_types = {}
                        for placeholder in mapping.keys():
                            entity_type = placeholder.split("_")[0].strip("[]")
                            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

                        print("Entities:")
                        for placeholder, original in mapping.items():
                            entity_type = placeholder.split("_")[0].strip("[]")
                            print(f"  • {entity_type}: {original} → {placeholder}")
                    else:
                        print("\n✓ No PII detected")

            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting interactive mode...")
                break
            except Exception as e:
                self._error(f"Unexpected error: {e}")

        return 0

    def cmd_list_policies(self, args: argparse.Namespace) -> int:
        """Execute list-policies command."""
        policies = list_policies()
        print("\nAvailable Policies:\n")
        for policy in policies:
            print(f"  • {policy}")
        print(f"\nTotal: {len(policies)} policies")
        return 0

    def cmd_list_detectors(self, args: argparse.Namespace) -> int:
        """Execute list-detectors command."""
        detectors = list_detectors()
        print("\nAvailable Detectors:\n")
        for detector in detectors:
            print(f"  • {detector}")
        print(f"\nTotal: {len(detectors)} detectors")
        return 0

    def cmd_validate_policy(self, args: argparse.Namespace) -> int:
        """Execute validate-policy command."""
        if yaml is None:
            self._error("PyYAML is required for policy validation. Install with: pip install pyyaml")
            return 1

        try:
            with open(args.policy_file, "r", encoding="utf-8") as f:
                policy_data = yaml.safe_load(f)

            # Basic validation
            errors = []

            if not isinstance(policy_data, dict):
                errors.append("Policy file must contain a dictionary")
            elif "entities" not in policy_data:
                errors.append("Policy must contain 'entities' key")
            elif not isinstance(policy_data["entities"], list):
                errors.append("'entities' must be a list")
            else:
                # Validate each entity
                for i, entity in enumerate(policy_data["entities"]):
                    if not isinstance(entity, dict):
                        errors.append(f"Entity {i} must be a dictionary")
                        continue
                    if "type" not in entity:
                        errors.append(f"Entity {i} missing 'type' field")
                    if "action" not in entity:
                        errors.append(f"Entity {i} missing 'action' field")
                    elif entity["action"] not in ("anonymize", "allow", "deny"):
                        errors.append(
                            f"Entity {i} has invalid action: {entity['action']}"
                        )

            if errors:
                print(f"\n❌ Policy validation failed:\n")
                for error in errors:
                    print(f"  • {error}")
                return 1
            else:
                self._success(f"Policy file is valid: {args.policy_file}")
                print(f"\nPolicy contains {len(policy_data['entities'])} entity definitions")
                return 0

        except Exception as e:
            self._error(f"Failed to validate policy: {e}")
            return 1

    def cmd_benchmark(self, args: argparse.Namespace) -> int:
        """Execute benchmark command."""
        import time

        test_texts = [
            "Contact John Doe at john.doe@example.com or 555-123-4567",
            "SSN: 123-45-6789, Credit Card: 4532-1488-0343-6467",
            "IP Address: 192.168.1.1, URL: https://example.com/path",
            "My name is Alice Smith and I live in New York City",
            "Call me at +1-800-555-0123 or email alice@company.org",
        ]

        detectors_to_test = [args.detector] if args.detector else list_detectors()

        print(f"\n⚡ Benchmark Results ({args.iterations} iterations per test):\n")

        for detector in detectors_to_test:
            try:
                guard = PromptGuard(policy="default_pii", detectors=[detector])

                total_time = 0.0
                for _ in range(args.iterations):
                    for text in test_texts:
                        start = time.perf_counter()
                        guard.anonymize(text)
                        total_time += time.perf_counter() - start

                avg_time_ms = (total_time / (args.iterations * len(test_texts))) * 1000
                throughput = (args.iterations * len(test_texts)) / total_time

                print(f"Detector: {detector}")
                print(f"  Average latency: {avg_time_ms:.3f} ms")
                print(f"  Throughput:      {throughput:.1f} req/s")
                print()

            except Exception as e:
                self._error(f"Failed to benchmark {detector}: {e}")

        return 0

    def run(self, argv: Optional[List[str]] = None) -> int:
        """Run the CLI with provided arguments."""
        args = self.parser.parse_args(argv)

        if not args.command:
            self.parser.print_help()
            return 1

        # Dispatch to command handler
        command_method = getattr(self, f"cmd_{args.command.replace('-', '_')}", None)
        if command_method:
            return command_method(args)
        else:
            self._error(f"Unknown command: {args.command}")
            return 1


def main():
    """Main entry point for CLI."""
    cli = PromptGuardCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
