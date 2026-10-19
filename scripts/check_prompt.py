"""Interactive CLI Tool to check any prompt for contradictions in the terminal.

Usage:
  python scripts/check_prompt.py "Write exactly 100 words, but fewer than 80 words."
  python scripts/check_prompt.py --interactive
  python scripts/check_prompt.py --mode rules "..."
  python scripts/check_prompt.py --mode hybrid "..."
"""

import sys
import argparse
from pathlib import Path

# Ensure package is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from contradictprompt.engine import analyze
from contradictprompt.repair import suggestions
from contradictprompt.models import Label
from contradictprompt.llm import LLMClient


def format_colored(text: str, color: str) -> str:
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_assessment(prompt: str, mode: str = "rules"):
    print("\n" + "=" * 78)
    print(format_colored(" CONTRADICTPROMPT — PROMPT CONSISTENCY ANALYSIS", "bold"))
    print("=" * 78)
    print(f"Input Prompt:\n\"{format_colored(prompt.strip(), 'cyan')}\"\n")

    client = None
    if mode in ("hybrid", "llm"):
        client = LLMClient()

    assessment = analyze(prompt, mode=mode, client=client)

    label_str = assessment.label.value if hasattr(assessment.label, "value") else str(assessment.label)
    label_colors = {
        "Compatible": "green",
        "Partially conflicting": "yellow",
        "Fully impossible": "red",
        "Underspecified": "magenta",
    }
    color = label_colors.get(label_str, "cyan")

    print("-" * 78)
    print(f"Classification Label : {format_colored(label_str.upper(), color)}")
    print(f"Analysis Mode        : {assessment.mode} (Latency: {assessment.latency_ms:.2f} ms)")
    print(f"Explanation          : {assessment.explanation}")

    if assessment.secondary_flags:
        print(f"Secondary Flags      : {', '.join(assessment.secondary_flags)}")

    if assessment.clarification_questions:
        print(format_colored("Clarification Required:", "magenta"))
        for q in assessment.clarification_questions:
            print(f"  • {q}")

    print("-" * 78)
    print(f"Extracted Instructions ({len(assessment.instructions)}):")
    for ins in assessment.instructions:
        bounds_str = f"bounds={ins.bounds}" if hasattr(ins, "bounds") and ins.bounds else ""
        print(f"  • [{ins.id}] (scope={ins.scope}, kind={ins.kind} {bounds_str}):")
        print(f"    \"{ins.text}\"")

    if assessment.conflicts:
        print("-" * 78)
        print(f"Detected Conflicts ({len(assessment.conflicts)}):")
        for i, c in enumerate(assessment.conflicts, 1):
            sev_color = "red" if c.severity == "hard" else "yellow"
            print(f"  Conflict #{i} [{format_colored(c.severity.upper(), sev_color)} - {c.kind}]:")
            print(f"    Explanation : {c.explanation}")
            print(f"    Between IDs : {c.instruction_ids}")

    if assessment.constraint_graph and assessment.constraint_graph.edges:
        print("-" * 78)
        print("Constraint Graph Edges:")
        for edge in assessment.constraint_graph.edges:
            print(f"  • {edge.source} --({edge.relation})--> {edge.target}")

    if assessment.minimal_conflicting_sets:
        print("-" * 78)
        print(format_colored(f"Minimal Conflicting Sets: {assessment.minimal_conflicting_sets}", "red"))

    # Repair suggestions if conflicting
    if label_str in ("Fully impossible", "Partially conflicting"):
        repairs = suggestions(assessment)
        if repairs:
            print("-" * 78)
            print(format_colored("Proposed Intent-Preserving Repairs:", "yellow"))
            for i, rep in enumerate(repairs, 1):
                print(f"  Option {i} [{rep.id}]: {rep.description}")
                print(f"  Repaired Prompt: \"{format_colored(rep.prompt, 'green')}\"")

    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="ContradictPrompt Terminal Checker")
    parser.add_argument("prompt", nargs="?", default=None, help="The prompt to analyze")
    parser.add_argument("--mode", choices=["rules", "hybrid", "llm"], default="rules", help="Engine mode (default: rules)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive terminal mode")

    args = parser.parse_args()

    if args.interactive or not args.prompt:
        print(format_colored("\n--- ContradictPrompt Interactive Terminal ---", "bold"))
        print("Type a prompt and press Enter to analyze. Type 'exit' or 'quit' to stop.\n")
        while True:
            try:
                user_prompt = input(format_colored("Enter prompt > ", "bold")).strip()
                if not user_prompt:
                    continue
                if user_prompt.lower() in ("exit", "quit", "q"):
                    print("Exiting.")
                    break
                print_assessment(user_prompt, mode=args.mode)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break
    else:
        print_assessment(args.prompt, mode=args.mode)


if __name__ == "__main__":
    main()
