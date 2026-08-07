import pandas as pd


# ── Tool Metadata ──────────────────────────────────────────────────────────────
# Each tool exposes a `name`, `description`, and `args_schema` so the LLM agent
# can understand what it does and when to invoke it.
# ──────────────────────────────────────────────────────────────────────────────


def load_contract_dataframe(csv_path: str) -> pd.DataFrame:
    """Load a contract CSV file into a pandas DataFrame."""
    df = pd.read_csv(csv_path)
    return df


def summarize_contract_dataframe(df: pd.DataFrame) -> str:
    """Return a statistical summary of the contract DataFrame."""
    if df.empty:
        return "The contract dataframe is empty."
    summary = df.describe(include="all").transpose()
    return summary.to_string()


def detect_contract_risk_clauses(df: pd.DataFrame) -> str:
    """Detect columns related to risk or compliance in the contract DataFrame."""
    if df.empty:
        return "The contract dataframe is empty."
    risk_columns = [
        col for col in df.columns
        if "risk" in col.lower() or "compliance" in col.lower()
    ]
    if not risk_columns:
        return "No explicit risk or compliance columns found in the contract dataframe."
    risks = df[risk_columns].head(10).to_string(index=False)
    return f"Detected risk-related columns: {risk_columns}\n{risks}"


class PandasAuditTool:
    """
    Tool to audit a contract CSV using pandas.
    Summarises the dataframe and detects risk / compliance columns.
    """

    # ── Tool metadata (used by agent tool-selection logic) ────────────────────
    name: str = "pandas_contract_audit"
    description: str = (
        "Use this tool when the task involves a CSV or spreadsheet contract file. "
        "It summarises the data and highlights risk or compliance-related columns."
    )
    args_schema: dict = {
        "contract_csv_path": {
            "type": "string",
            "description": "Absolute or relative path to the contract CSV file.",
        }
    }
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def run(state: dict) -> dict:
        contract_csv = state.get("contract_csv_path")
        if not contract_csv:
            state["pandas_tool_result"] = "No contract CSV path provided in state."
            state["tool_errors"] = state.get("tool_errors", []) + [
                "PandasAuditTool: missing 'contract_csv_path' in state."
            ]
            return state

        try:
            df = load_contract_dataframe(contract_csv)
            state["contract_dataframe_summary"] = summarize_contract_dataframe(df)
            state["contract_risk_clause_detection"] = detect_contract_risk_clauses(df)
            state["pandas_tool_result"] = "Pandas audit tool executed successfully."
        except FileNotFoundError:
            msg = f"PandasAuditTool: file not found at path '{contract_csv}'."
            state["pandas_tool_result"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]
        except Exception as exc:
            msg = f"PandasAuditTool: unexpected error — {exc}"
            state["pandas_tool_result"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]

        return state
