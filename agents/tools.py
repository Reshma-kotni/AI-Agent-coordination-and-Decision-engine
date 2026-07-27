import pandas as pd


def load_contract_dataframe(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df


def summarize_contract_dataframe(df: pd.DataFrame) -> str:
    if df.empty:
        return "The contract dataframe is empty."
    summary = df.describe(include="all").transpose()
    return summary.to_string()


def detect_contract_risk_clauses(df: pd.DataFrame) -> str:
    if df.empty:
        return "The contract dataframe is empty."
    risk_columns = [col for col in df.columns if "risk" in col.lower() or "compliance" in col.lower()]
    if not risk_columns:
        return "No explicit risk or compliance columns found in the contract dataframe."
    risks = df[risk_columns].head(10).to_string(index=False)
    return f"Detected risk-related columns: {risk_columns}\n{risks}"


class PandasAuditTool:
    @staticmethod
    def run(state):
        contract_csv = state.get("contract_csv_path")
        if not contract_csv:
            state["pandas_tool_result"] = "No contract CSV path provided."
            return state

        try:
            df = load_contract_dataframe(contract_csv)
            state["contract_dataframe_summary"] = summarize_contract_dataframe(df)
            state["contract_risk_clause_detection"] = detect_contract_risk_clauses(df)
            state["pandas_tool_result"] = "Pandas audit tool executed successfully."
        except Exception as exc:
            state["pandas_tool_result"] = f"Pandas audit tool failed: {exc}"
        return state
