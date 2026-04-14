"""
AI Cyber Assurance Agent — CLI entry point.

Usage:
    python main.py                                          # uses data/sample_input.json
    python main.py --input data/sample_input.json          # explicit JSON file
    python main.py --control "..." --requirement "..." --evidence "..."
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="AI Cyber Assurance Agent — multi-agent security control assessment CLI",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        help="Path to a JSON file containing control, requirement, and evidence.",
    )
    parser.add_argument(
        "--control",
        metavar="TEXT",
        help="Control description [C].",
    )
    parser.add_argument(
        "--requirement",
        metavar="TEXT",
        help="Requirement [Dx].",
    )
    parser.add_argument(
        "--evidence",
        metavar="TEXT",
        help="Evidence [Ex].",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Optional path to write the JSON output to a file.",
    )
    return parser


def load_input(args: argparse.Namespace) -> dict:
    """Load audit input from CLI arguments or a JSON file."""
    if args.control and args.requirement and args.evidence:
        return {
            "control": args.control,
            "requirement": args.requirement,
            "evidence": args.evidence,
        }

    if args.input:
        input_path = Path(args.input)
    else:
        # Default to sample input
        input_path = Path(__file__).resolve().parent / "data" / "sample_input.json"
        print(f"No input specified — using sample: {input_path}")

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    required_keys = {"control", "requirement", "evidence"}
    missing = required_keys - set(data.keys())
    if missing:
        print(
            f"Error: Input file is missing required keys: {missing}", file=sys.stderr
        )
        sys.exit(1)

    return data


def print_report(result: dict) -> None:
    """Print a formatted human-readable audit report to stdout."""
    SEP = "=" * 72
    sep = "-" * 72

    assessment = result.get("requirement_assessment", "Unknown")
    emoji_map = {"Met": "✅", "Partially Met": "⚠️ ", "Not Met": "❌"}
    emoji = emoji_map.get(assessment, "❓")

    print(f"\n{SEP}")
    print("  AI CYBER ASSURANCE AGENT — AUDIT REPORT")
    print(SEP)

    print(f"\n{emoji}  REQUIREMENT ASSESSMENT: {assessment.upper()}")

    print(f"\n{sep}")
    print("CONTROL OBJECTIVE")
    print(sep)
    print(result.get("control_objective", "N/A"))

    print(f"\n{sep}")
    print("EVIDENCE QUALITY")
    print(sep)
    eq = result.get("evidence_quality", {})
    print(f"  Completeness : {eq.get('completeness', 'N/A')}")
    print(f"  Relevance    : {eq.get('relevance', 'N/A')}")
    print(f"  Reliability  : {eq.get('reliability', 'N/A')}")

    gaps = result.get("gaps_identified", [])
    print(f"\n{sep}")
    print(f"GAPS IDENTIFIED ({len(gaps)})")
    print(sep)
    if gaps:
        for i, gap in enumerate(gaps, 1):
            print(f"  {i}. {gap}")
    else:
        print("  No significant gaps identified.")

    recs = result.get("recommendations", [])
    print(f"\n{sep}")
    print(f"RECOMMENDATIONS ({len(recs)})")
    print(sep)
    if recs:
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec}")
    else:
        print("  No specific recommendations.")

    print(f"\n{sep}")
    print("AUDIT OPINION")
    print(sep)
    print(result.get("audit_opinion", "N/A"))

    questions = result.get("follow_up_questions", [])
    print(f"\n{sep}")
    print(f"FOLLOW-UP QUESTIONS ({len(questions)})")
    print(sep)
    if questions:
        for i, q in enumerate(questions, 1):
            print(f"  Q{i}: {q}")
    else:
        print("  No follow-up questions required.")

    print(f"\n{SEP}\n")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_data = load_input(args)

    print("\nInitialising AI Cyber Assurance Agent...")
    print("Running 3-agent audit pipeline (Auditor → Reviewer → Questioning)...")
    print("This typically takes 20–40 seconds.\n")

    try:
        from agents.pipeline import AuditPipeline

        pipeline = AuditPipeline()
        result = pipeline.run(input_data)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)

    print_report(result)

    # Write JSON output to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"JSON output written to: {output_path}")
    else:
        print("Raw JSON Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
