"""
main.py
───────
Entry point for the AI Agent Coordination & Decision Engine.
Milestone 2 — Sprint 2

Demonstrates three audit scenarios:
  1. Standard task (no files)         → LLM tool router decides tools needed
  2. CSV contract audit               → PandasAuditTool invoked
  3. PDF + Vendor API audit           → PDFContractParserTool + VendorRiskApiTool invoked

Usage:
  python main.py
  python main.py --mode csv
  python main.py --mode pdf
"""

import argparse
from workflows.Orchestrator import Orchestrator


def run_standard(orchestrator: Orchestrator):
    task = (
        "Audit the latest vendor contract from Initech Solutions for procurement risk "
        "and summarize required review steps. Verify the vendor's compliance history."
    )
    print(f"\n[Mode] Standard Task (LLM-driven tool selection)")
    print(f"[Task] {task}")
    state = orchestrator.run(task, vendor_name="Initech Solutions")
    _print_summary(state)


def run_csv(orchestrator: Orchestrator):
    task = (
        "Audit the vendor pricing spreadsheet at 'sample_contract.csv' "
        "for cost anomalies and compliance risks."
    )
    print(f"\n[Mode] CSV Contract Audit")
    print(f"[Task] {task}")
    state = orchestrator.run(task, contract_csv_path="sample_contract.csv")
    _print_summary(state)


def run_pdf(orchestrator: Orchestrator):
    task = (
        "Audit the vendor contract PDF at 'sample_contract.pdf' from Globex Ltd. "
        "Extract clauses, identify risk areas, and verify vendor standing."
    )
    print(f"\n[Mode] PDF + Vendor API Audit")
    print(f"[Task] {task}")
    state = orchestrator.run(
        task,
        contract_pdf_path="sample_contract.pdf",
        vendor_name="Globex Ltd",
    )
    _print_summary(state)


def _print_summary(state: dict):
    print("\n─── Audit Summary ───")
    print(f"  Validation Status : {state.get('validation_status', 'N/A')}")
    print(f"  Validation Errors : {state.get('validation_errors', [])}")
    print(f"  Tool Errors       : {state.get('tool_errors', [])}")
    print(f"  Report Path       : {state.get('report_path', 'N/A')}")
    print(f"  Node History      : {state.get('node_history', [])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Agent Audit Engine — Sprint 2")
    parser.add_argument(
        "--mode",
        choices=["standard", "csv", "pdf"],
        default="standard",
        help="Which audit scenario to run (default: standard)",
    )
    args = parser.parse_args()

    orchestrator = Orchestrator()

    if args.mode == "csv":
        run_csv(orchestrator)
    elif args.mode == "pdf":
        run_pdf(orchestrator)
    else:
        run_standard(orchestrator)
