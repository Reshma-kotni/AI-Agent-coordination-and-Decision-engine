"""
prompt_templates.py
───────────────────
Centralised prompt templates for all agent nodes.

Sprint 2: Tool-routing and error-recovery prompts.
Sprint 3: Memory-aware prompts — all key agents now receive:
  - vendor_history      : past audit records for this vendor (long-term memory)
  - risk_patterns       : matched known risk patterns from knowledge base
  - conversation_history: recent short-term buffer from this audit run
"""

# ── Planner ────────────────────────────────────────────────────────────────────
PLANNER_PROMPT = (
    "You are a planner agent for contract audit workflows.\n"
    "Break the incoming task into concrete audit steps.\n\n"
    "Task:\n"
    "{task}\n\n"
    "Available tools:\n"
    "{tools_summary}\n\n"
    "Vendor History (from long-term memory):\n"
    "{vendor_history}\n\n"
    "Provide a concise numbered plan and identify which tools will likely be needed. "
    "Take the vendor history into account when prioritising risk areas."
)

# ── Retriever / Tool Router ────────────────────────────────────────────────────
TOOL_ROUTER_PROMPT = (
    "You are a tool-selection agent for a contract audit system.\n"
    "Given the task description and audit plan, decide which tools to invoke.\n\n"
    "Task:\n"
    "{task}\n\n"
    "Audit Plan:\n"
    "{plan}\n\n"
    "Available Tools:\n"
    "{tools_summary}\n\n"
    "Respond with a JSON object listing the tools to invoke and the arguments for each.\n"
    "Example response:\n"
    "{{\n"
    '  "tools_to_invoke": [\n'
    '    {{"tool": "pdf_contract_parser", "args": {{"contract_pdf_path": "contract.pdf"}}}},\n'
    '    {{"tool": "vendor_risk_api", "args": {{"vendor_name": "Acme Corp"}}}}\n'
    "  ]\n"
    "}}\n"
    "If no tools are needed, return: {{\"tools_to_invoke\": []}}"
)

# ── Analyzer ───────────────────────────────────────────────────────────────────
ANALYZER_PROMPT = (
    "You are an analyzer agent for vendor contracts.\n"
    "Extract risk signals, compliance issues, and contract summary details from the retrieved text.\n\n"
    "Retrieved text:\n"
    "{retrieval_text}\n\n"
    "Vendor Risk Report (if available):\n"
    "{vendor_risk_report}\n\n"
    "Vendor History (from long-term memory):\n"
    "{vendor_history}\n\n"
    "Known Risk Patterns (from knowledge base):\n"
    "{known_risk_patterns}\n\n"
    "Recent Audit Context (short-term memory):\n"
    "{conversation_history}\n\n"
    "Summarize the key audit concerns, identifying:\n"
    "1. Compliance risks\n"
    "2. Financial risks\n"
    "3. Operational risks\n"
    "4. Legal / liability risks\n"
    "Reference the vendor history and known patterns where relevant."
)

# ── Decision ───────────────────────────────────────────────────────────────────
DECISION_PROMPT = (
    "You are a decision agent for procurement auditing.\n"
    "Based on the analysis and historical context, recommend the next audit action.\n\n"
    "Analysis:\n"
    "{analysis_text}\n\n"
    "Vendor History (from long-term memory):\n"
    "{vendor_history}\n\n"
    "Known Risk Patterns:\n"
    "{known_risk_patterns}\n\n"
    "Tool Errors (if any):\n"
    "{tool_errors}\n\n"
    "Provide a short, specific recommendation with next steps, owners, and deadlines. "
    "If this vendor has a history of issues, escalate the recommendation accordingly."
)

# ── Error Recovery ─────────────────────────────────────────────────────────────
ERROR_RECOVERY_PROMPT = (
    "You are an error recovery agent in a contract audit pipeline.\n"
    "The following tools encountered errors during execution:\n\n"
    "{tool_errors}\n\n"
    "Original task:\n"
    "{task}\n\n"
    "Suggest corrected tool arguments or an alternative approach to complete the audit.\n"
    "Respond in plain text."
)

# ── Research Query Generation (used by ResearchAgent internally) ───────────────
RESEARCH_QUERY_GEN_PROMPT = (
    "You are a research strategist for a contract audit team.\n"
    "Generate {n} short, targeted web search queries to help an auditor understand:\n"
    "  1. Regulatory/compliance context for this vendor and contract type.\n"
    "  2. Background on the vendor (news, reputation, risk incidents).\n"
    "  3. Industry benchmarks for this type of procurement.\n\n"
    "Task: {task}\n\n"
    "Audit Plan (excerpt):\n"
    "{plan_excerpt}\n\n"
    "Known Vendor History:\n"
    "{vendor_history}\n\n"
    "Output ONLY a numbered list of queries, one per line. No explanations."
)
