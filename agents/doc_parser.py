"""
doc_parser.py
─────────────
PDFContractParserTool — Enterprise Tool for extracting text from PDF vendor
contracts and breaking them into manageable chunks for downstream analysis.

Dependencies: pypdf
"""

from __future__ import annotations

import os


class PDFContractParserTool:
    """
    Reads a local PDF contract file, extracts plain text from each page,
    and stores the full text plus a chunked version in the shared agent state.

    Tool Metadata (used by the LLM agent for intelligent tool selection)
    ────────────────────────────────────────────────────────────────────
    name        : pdf_contract_parser
    description : Use this tool when the task involves a PDF vendor contract
                  or legal document that must be read and analysed. It extracts
                  raw contract text from the PDF so the Analyzer agent can review it.
    args_schema : { "contract_pdf_path": { "type": "string",
                    "description": "Path to the PDF contract file." } }
    """

    name: str = "pdf_contract_parser"
    description: str = (
        "Use this tool when the task involves a PDF vendor contract or legal document. "
        "It extracts the full text from the PDF so the Analyzer agent can review it."
    )
    args_schema: dict = {
        "contract_pdf_path": {
            "type": "string",
            "description": "Absolute or relative path to the PDF contract file.",
        }
    }

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(pdf_path: str) -> str:
        """Extract text from all pages of a PDF using pypdf."""
        try:
            from pypdf import PdfReader  # lazy import — only required when tool is used
        except ImportError as exc:
            raise ImportError(
                "pypdf is required for PDF parsing. Run: pip install pypdf"
            ) from exc

        reader = PdfReader(pdf_path)
        pages_text = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages_text.append(f"--- Page {page_num} ---\n{text.strip()}")
        return "\n\n".join(pages_text)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 2000) -> list[str]:
        """Split text into chunks of `chunk_size` characters for LLM context windows."""
        return [text[i: i + chunk_size] for i in range(0, len(text), chunk_size)]

    # ── Public interface ──────────────────────────────────────────────────────

    @staticmethod
    def run(state: dict) -> dict:
        """
        Main entry point called by the Orchestrator.
        Reads `contract_pdf_path` from state, extracts text, and writes results
        back to state under `pdf_contract_text` and `pdf_contract_chunks`.
        """
        pdf_path = state.get("contract_pdf_path")

        if not pdf_path:
            msg = "PDFContractParserTool: no 'contract_pdf_path' provided in state."
            state["pdf_tool_result"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]
            return state

        if not os.path.exists(pdf_path):
            msg = f"PDFContractParserTool: file not found at '{pdf_path}'."
            state["pdf_tool_result"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]
            return state

        try:
            full_text = PDFContractParserTool._extract_text(pdf_path)
            chunks = PDFContractParserTool._chunk_text(full_text)

            state["pdf_contract_text"] = full_text
            state["pdf_contract_chunks"] = chunks
            state["pdf_tool_result"] = (
                f"PDF parsed successfully: {len(chunks)} chunk(s) extracted "
                f"from '{os.path.basename(pdf_path)}'."
            )

            # Make the first 2 chunks available as retrieval context for the Analyzer
            state["retrieval"] = "\n\n".join(chunks[:2])

        except Exception as exc:
            msg = f"PDFContractParserTool: unexpected error — {exc}"
            state["pdf_tool_result"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]

        return state
