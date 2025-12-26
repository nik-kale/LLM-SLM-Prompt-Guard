"""
CLI interface for Prompt Guard - Quick PII detection and anonymization.
"""

import sys
import json
import pathlib
from typing import Optional
import click
from . import PromptGuard, get_version, list_policies, list_detectors
from .types import DetectorResult


@click.group()
@click.version_option(version=get_version(), prog_name="prompt-guard")
def cli():
    """Prompt Guard CLI - Enterprise-grade PII protection for LLM applications."""
    pass


@cli.command()
@click.argument("text", required=False)
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Read text from file instead"
)
@click.option(
    "--policy", "-p", default="default_pii", help="Policy to use (default: default_pii)"
)
@click.option(
    "--detectors",
    "-d",
    default="regex",
    help="Comma-separated detector list (default: regex)",
)
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.5,
    help="Minimum confidence threshold for ML detectors (default: 0.5)",
)
@click.option("--json-output", "-j", is_flag=True, help="Output results as JSON")
def detect(
    text: Optional[str],
    file: Optional[str],
    policy: str,
    detectors: str,
    confidence: float,
    json_output: bool,
):
    """Detect PII entities in text or file."""
    # Get input text
    if file:
        with open(file, "r", encoding="utf-8") as f:
            input_text = f.read()
    elif text:
        input_text = text
    else:
        # Read from stdin
        input_text = sys.stdin.read()

    if not input_text.strip():
        click.echo("Error: No input text provided", err=True)
        sys.exit(1)

    # Initialize guard
    detector_list = [d.strip() for d in detectors.split(",")]
    try:
        guard = PromptGuard(detectors=detector_list, policy=policy)
    except Exception as e:
        click.echo(f"Error initializing PromptGuard: {e}", err=True)
        sys.exit(1)

    # Detect entities
    all_results = []
    for detector in guard.detectors:
        all_results.extend(detector.detect(input_text))

    # Filter by confidence if applicable
    filtered_results = [
        r for r in all_results if r.confidence is None or r.confidence >= confidence
    ]

    if json_output:
        output = {
            "total_entities": len(filtered_results),
            "entities": [
                {
                    "type": r.entity_type,
                    "text": r.text,
                    "start": r.start,
                    "end": r.end,
                    "confidence": r.confidence,
                }
                for r in filtered_results
            ],
            "summary": {},
        }
        # Count by type
        for r in filtered_results:
            output["summary"][r.entity_type] = (
                output["summary"].get(r.entity_type, 0) + 1
            )
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\n{'=' * 60}")
        click.echo(f"PII Detection Results")
        click.echo(f"{'=' * 60}\n")
        click.echo(f"Total entities found: {len(filtered_results)}\n")

        if filtered_results:
            # Group by type
            by_type = {}
            for r in filtered_results:
                if r.entity_type not in by_type:
                    by_type[r.entity_type] = []
                by_type[r.entity_type].append(r)

            for entity_type, entities in sorted(by_type.items()):
                click.echo(f"{entity_type}: {len(entities)} found")
                for i, r in enumerate(entities, 1):
                    conf_str = (
                        f" (confidence: {r.confidence:.2f})"
                        if r.confidence is not None
                        else ""
                    )
                    click.echo(
                        f"  {i}. '{r.text}' at position {r.start}-{r.end}{conf_str}"
                    )
                click.echo()
        else:
            click.echo("No PII entities detected.\n")


@cli.command()
@click.argument("text", required=False)
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Read text from file instead"
)
@click.option(
    "--output", "-o", type=click.Path(), help="Write anonymized text to file"
)
@click.option(
    "--mapping-output",
    "-m",
    type=click.Path(),
    help="Write mapping to JSON file for de-anonymization",
)
@click.option(
    "--policy", "-p", default="default_pii", help="Policy to use (default: default_pii)"
)
@click.option(
    "--detectors",
    "-d",
    default="regex",
    help="Comma-separated detector list (default: regex)",
)
@click.option("--json-output", "-j", is_flag=True, help="Output results as JSON")
def anonymize(
    text: Optional[str],
    file: Optional[str],
    output: Optional[str],
    mapping_output: Optional[str],
    policy: str,
    detectors: str,
    json_output: bool,
):
    """Anonymize PII in text or file."""
    # Get input text
    if file:
        with open(file, "r", encoding="utf-8") as f:
            input_text = f.read()
    elif text:
        input_text = text
    else:
        # Read from stdin
        input_text = sys.stdin.read()

    if not input_text.strip():
        click.echo("Error: No input text provided", err=True)
        sys.exit(1)

    # Initialize guard
    detector_list = [d.strip() for d in detectors.split(",")]
    try:
        guard = PromptGuard(detectors=detector_list, policy=policy)
    except Exception as e:
        click.echo(f"Error initializing PromptGuard: {e}", err=True)
        sys.exit(1)

    # Anonymize
    anonymized_text, mapping = guard.anonymize(input_text)

    if json_output:
        result = {
            "anonymized_text": anonymized_text,
            "mapping": mapping,
            "entity_count": len(mapping),
        }
        output_str = json.dumps(result, indent=2)
    else:
        output_str = anonymized_text

    # Write or print output
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_str)
        click.echo(f"Anonymized text written to: {output}")
    else:
        click.echo(output_str)

    # Write mapping if requested
    if mapping_output:
        with open(mapping_output, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)
        click.echo(f"Mapping written to: {mapping_output}")


@cli.command()
@click.argument("text", required=False)
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Read text from file instead"
)
@click.option(
    "--mapping",
    "-m",
    type=click.Path(exists=True),
    required=True,
    help="JSON file containing mapping from anonymize",
)
@click.option(
    "--output", "-o", type=click.Path(), help="Write de-anonymized text to file"
)
def deanonymize(
    text: Optional[str], file: Optional[str], mapping: str, output: Optional[str]
):
    """Restore original PII from anonymized text using mapping."""
    # Get input text
    if file:
        with open(file, "r", encoding="utf-8") as f:
            input_text = f.read()
    elif text:
        input_text = text
    else:
        # Read from stdin
        input_text = sys.stdin.read()

    if not input_text.strip():
        click.echo("Error: No input text provided", err=True)
        sys.exit(1)

    # Load mapping
    with open(mapping, "r", encoding="utf-8") as f:
        mapping_dict = json.load(f)

    # Initialize guard (minimal setup, we just need deanonymize method)
    guard = PromptGuard()

    # De-anonymize
    original_text = guard.deanonymize(input_text, mapping_dict)

    # Write or print output
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(original_text)
        click.echo(f"De-anonymized text written to: {output}")
    else:
        click.echo(original_text)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--pattern", "-p", default="*.txt", help="File pattern to match (default: *.txt)"
)
@click.option(
    "--policy", default="default_pii", help="Policy to use (default: default_pii)"
)
@click.option(
    "--detectors",
    "-d",
    default="regex",
    help="Comma-separated detector list (default: regex)",
)
@click.option("--recursive", "-r", is_flag=True, help="Scan directories recursively")
@click.option("--json-output", "-j", is_flag=True, help="Output results as JSON")
def scan(
    directory: str,
    pattern: str,
    policy: str,
    detectors: str,
    recursive: bool,
    json_output: bool,
):
    """Scan directory for PII in files."""
    dir_path = pathlib.Path(directory)
    detector_list = [d.strip() for d in detectors.split(",")]

    try:
        guard = PromptGuard(detectors=detector_list, policy=policy)
    except Exception as e:
        click.echo(f"Error initializing PromptGuard: {e}", err=True)
        sys.exit(1)

    # Find files
    if recursive:
        files = dir_path.rglob(pattern)
    else:
        files = dir_path.glob(pattern)

    results = {}
    total_files = 0
    total_entities = 0

    for file_path in files:
        if not file_path.is_file():
            continue

        total_files += 1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Detect entities
            all_results = []
            for detector in guard.detectors:
                all_results.extend(detector.detect(content))

            if all_results:
                total_entities += len(all_results)
                results[str(file_path)] = {
                    "entity_count": len(all_results),
                    "entities": [
                        {
                            "type": r.entity_type,
                            "text": r.text,
                            "start": r.start,
                            "end": r.end,
                            "confidence": r.confidence,
                        }
                        for r in all_results
                    ],
                }
        except Exception as e:
            if json_output:
                results[str(file_path)] = {"error": str(e)}
            else:
                click.echo(f"Error scanning {file_path}: {e}", err=True)

    if json_output:
        output = {
            "total_files_scanned": total_files,
            "files_with_pii": len(results),
            "total_entities": total_entities,
            "results": results,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\n{'=' * 60}")
        click.echo(f"PII Scan Results")
        click.echo(f"{'=' * 60}\n")
        click.echo(f"Files scanned: {total_files}")
        click.echo(f"Files with PII: {len(results)}")
        click.echo(f"Total entities found: {total_entities}\n")

        if results:
            for file_path, file_results in results.items():
                if "error" in file_results:
                    click.echo(f"❌ {file_path}: Error - {file_results['error']}")
                else:
                    click.echo(
                        f"⚠️  {file_path}: {file_results['entity_count']} entities"
                    )
                    # Group by type
                    by_type = {}
                    for entity in file_results["entities"]:
                        entity_type = entity["type"]
                        by_type[entity_type] = by_type.get(entity_type, 0) + 1
                    for entity_type, count in sorted(by_type.items()):
                        click.echo(f"    - {entity_type}: {count}")
                    click.echo()


@cli.command()
@click.argument("policy_file", type=click.Path(exists=True))
def validate_policy(policy_file: str):
    """Validate a custom policy YAML file."""
    try:
        guard = PromptGuard(custom_policy_path=policy_file)
        click.echo(f"✅ Policy file is valid: {policy_file}")

        # Show policy details
        click.echo(f"\nPolicy name: {guard.policy.get('name', 'Unnamed')}")
        click.echo(f"Description: {guard.policy.get('description', 'No description')}")

        entities = guard.policy.get("entities", {})
        click.echo(f"\nConfigured entities: {len(entities)}")
        for entity_type in sorted(entities.keys()):
            click.echo(f"  - {entity_type}")

    except Exception as e:
        click.echo(f"❌ Invalid policy file: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_policies_cmd():
    """List all available built-in policies."""
    policies = list_policies()
    click.echo(f"\nAvailable built-in policies ({len(policies)}):\n")
    for policy in sorted(policies):
        click.echo(f"  - {policy}")
    click.echo()


@cli.command()
def list_detectors_cmd():
    """List all available detectors and their status."""
    detectors = list_detectors()
    click.echo(f"\nAvailable detectors:\n")
    for name, available in sorted(detectors.items()):
        status = "✅ Available" if available else "❌ Not installed"
        click.echo(f"  {name}: {status}")
    click.echo()


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()

