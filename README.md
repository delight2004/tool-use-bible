# Tool-Use Pattern Showcase

This repository provides a practical guide to the "tool-use" pattern in AI, demonstrating two distinct implementation strategies: a simple, rule-based approach and a more advanced, LLM-driven approach.

## Overview

The "tool-use" pattern allows an AI agent to extend its capabilities by calling external functions (tools) to perform specific tasks, such as fetching data from an API, performing calculations, or accessing a database. This project breaks down the pattern into two clear examples.

---

### 1. Rule-Based Tool Use (Non-LLM)

This approach uses a straightforward, hard-coded system to map user intent to a specific function. It's fast, reliable, and perfect for applications where the range of user inputs is predictable.

**Relevant File:** `daily_verse_agent.py`

#### How It Works

1.  **Tool Registry:** A simple dictionary (`TOOL_REGISTRY`) maps function names to the actual Python functions.
2.  **Intent Parsing:** A parser (`parse_intent`) analyzes the user's input using basic string matching and regular expressions to determine which tool to call and what parameters to pass.
3.  **Execution:** The corresponding function is executed, and the result is returned to the user.

This method does not involve any large language models.

#### How to Run

```bash
python daily_verse_agent.py
```

---

### 2. LLM-Based Tool Use

This approach leverages a Large Language Model (LLM) to understand the user's intent and decide which tool to use. The LLM is given a list of available tools and their descriptions, and it generates a structured output (JSON) to specify the tool to call.

**Relevant Files:**
*   `tool.py`: The "toolbox" for the agent. This module defines the actual Python functions that call the Bible API (e.g., `fetch_daily_verse`) and includes the helper logic (`get_fn_signature`, `Tool` class) to format them for the LLM.
*   `tool_agent.py`: The "brain" of the operation. This is the core agent that manages the interaction between the user, the LLM (`gpt-oss-120b` via Groq), and the tools defined in `tool.py`.

#### How It Works

1.  **Tool Definition:** Python functions that interact with the Bible API are defined in `tool.py`. The `get_fn_signature` helper function inspects these functions and creates a JSON schema describing their purpose, parameters, and data types.
2.  **LLM Prompting:** The `ToolAgent` sends the user's query, along with the JSON schemas of all available tools, to the `gpt-oss-120b` model.
3.  **LLM Decision:** The LLM analyzes the user's intent and, if it determines a tool is needed, responds with a structured JSON object inside `<tool_code>` tags, specifying the exact tool to call and the arguments to use.
4.  **Execution & Validation:** The agent parses the LLM's response, validates the arguments to ensure they match the function's requirements, and then executes the chosen tool (e.g., calls the `search_topic` function).
5.  **Final Response:** The output from the tool (the "observation") is sent back to the LLM in a second API call. The LLM then uses this data to generate a final, polished, human-friendly response for the user.

#### Setup and Installation

1.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv biblenv
    .\biblenv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root of the `tool-use-bible` directory and add your Groq API key:
    ```
    GROQ_API_KEY="your-api-key-here"
    ```

#### How to Run

```bash
python tool_agent.py
```
