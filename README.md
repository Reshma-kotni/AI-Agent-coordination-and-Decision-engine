# AI Agent Coordination and Decision Engines

This repository contains a framework for multi-agent coordination and decision-making, designed specifically for complex tasks such as contract auditing and procurement risk analysis. The system leverages state management to pass context between specialized AI agents, orchestrating their workflow to produce actionable insights and detailed reports.

## Features

- **Multi-Agent Architecture**: A modular system featuring specialized agents (Planner, Retriever, Analyzer, Decision, Review, Executor, Validator).
- **State Management**: Uses an `AuditState` dictionary to pass state across agent nodes seamlessly.
- **Dynamic Tool Invocation**: Integrates tools like `PandasAuditTool` dynamically based on the analyzer agent's output.
- **Groq Integration**: Utilizes the powerful LLaMA models via the Groq API for rapid and efficient inference.
- **Conditional Workflows**: Incorporates branching logic (e.g., standard audit vs. high-risk review) based on analysis.
- **Automated Reporting**: Generates a comprehensive final report (`final_report.txt`) outlining the plan, retrieval, analysis, and decisions.

## Directory Structure

```
.
├── agents/
│   ├── analyzer.py       # Analyzes the retrieved information
│   ├── decision.py       # Makes decisions based on the analysis
│   ├── executor.py       # Executes final tasks and generates reports
│   ├── planner.py        # Plans the sequence of actions based on the task
│   ├── prompt_templates.py # Contains prompts for different agents
│   ├── retriever.py      # Retrieves relevant data for the task
│   ├── review.py         # Performs risk review if conditionally required
│   ├── tools.py          # Contains tools like PandasAuditTool
│   └── validator.py      # Validates the final state/output
├── workflows/
│   └── Orchestrator.py   # Manages the state and coordinates agents
├── main.py               # Main entry point to run the orchestrator
├── requirements.txt      # Project dependencies
├── test_orc.py           # Script for testing the orchestrator interactively
└── test_planner.py       # Script for testing the Groq API connection and planner
```

## Requirements

The project dependencies are listed in `requirements.txt`. They include:

- `groq`
- `python-dotenv`
- `duckduckgo_search`
- `pandas`
- `langchain`
- `langgraph`

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd ai-agent-coordination-and-decision-engines
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

You can run the default workflow by executing `main.py`:

```bash
python main.py
```

This will run an example task: *"Audit the latest vendor contract for procurement risk and summarize required review steps."*

The orchestrator will trigger the sequence of agents and tools, print the outputs at each stage, and ultimately generate a `final_report.txt` in the root directory.

### Interactive Testing

If you want to input a custom task, you can use the `test_orc.py` script:

```bash
python test_orc.py
```

You will be prompted to enter your task, and the orchestrator will process it accordingly.

### Testing API Connectivity

To ensure your Groq API key is set up correctly and the basic agent functionality is working, run:

```bash
python test_planner.py
```
