# 🧠 The Cloud Architecture Brain Trust

An open-source, multi-agent artificial intelligence system that autonomously **designs, secures, and cost-optimizes** your custom AWS cloud architectures. It leverages the latest **Agentic RAG pipelines** over official AWS documentation and employs a team of highly specialized Agent personas interacting entirely through open protocols (A2A and MCP).


## 🎯 Architecture & Technologies
This framework is built primarily on 100% free-tier, localized, and open integrations:
1. **Lead Architect (Orchestrator)**: Powered by Google's `gemini-2.5-flash` API. It drives the workflow, queries vector databases, and drafts the overall blueprint.
2. **Specialist Agents (Security & FinOps)**: Isolated microservices deployed via FastAPI running entirely local logic using Ollama's `qwen`. They communicate with the Architect via the **Agent-to-Agent (A2A) Protocol**.
3. **Agentic RAG Engine**: A highly accurate knowledge base pipeline that pulls the AWS Well-Architected Framework and processes it through a local LLM, converting it into rigorous semantic chunk rules stored in a **ChromaDB** vector instance via `nomic-embed-text`.
4. **Tool Integration**: Uses the **Model Context Protocol (MCP)** to expose the RAG Vector Database seamlessly back to the Orchestrator without tight coupling.
5. **Interactive UI**: A sleek **Streamlit** frontend allowing teams to visualize agent-to-agent feedback loops and download the final markdown blueprint.

---

## 🚀 Quickstart Guide

This implementation is highly modular. You can run all processes locally or within a contained Python environment. Ensure you have Python 3.9+ installed.

### 1. Prerequisites (Ollama Setup)
Since your FinOps and Security specialists run on 0-cost local hardware, make sure you have [Ollama](https://ollama.com/) running on your system.
```bash
ollama pull qwen
ollama pull nomic-embed-text
```

### 2. Environment Installation
Clone the repo, open a terminal, and install the Brain Trust dependencies.
```bash
# Create a virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install chromadb pypdf ollama mcp pydantic fastapi uvicorn requests google-genai streamlit textwrap3
```

### 3. Build the Agentic RAG Database 
Add any AWS architecture documentation (like the AWS Well-Architected PDF) into the `/data` folder. The pipeline will intelligently parse and chunk every PDF using the local LLM.
```bash
python phase1_data_pipeline.py
```
*(Optional) Verify the data vectorization:*
```bash
python view_db.py
```

### 4. Deploy the Local A2A Specialists
Boot up your FinOps and Security engineers. They will run independently on ports `9001` and `9002` waiting for drafts to review.
```bash
python phase3_specialists.py
```

### 5. Launch the Web App UI 🌐
In a **new terminal tab** (with your `venv` active), run the Streamlit frontend. Enter your Google Gemini API key inside the setup sidebar to wake up the Lead Architect.
```bash
streamlit run app.py
```
*Head over to `localhost:8501` to use the chat interface!*

---

## 🛠️ How it Works under the hood
1. **RAG Extraction**: `phase1` reads documents by roughly parsing 3500-char blocks. It forces `qwen` to extract pure JSON format architecture rules so the semantic context isn't littered with garbage text.
2. **MCP Abstraction**: `phase2` turns `ChromaDB` into a universal `search_aws_guidelines` tool available over `stdio` without hardcoding database drivers.
3. **A2A Interaction**: When you trigger a command on the frontend, the `Lead` creates an initial draft and does a POST request to Security. Security mandates changes, returns them, and the `Lead` queries Cost before compiling the final markdown solution.

![UML - Architecture of Cloud Architecture Brain Trust](https://github.com/yashkantharia/Cloud-Architecture-Brain-Trust/blob/main/UML.png)

## 🤝 Contributing
Want to add a Data Engineer agent or SRE Agent? You just need to build a new `uvicorn` router in `phase3` and append the POST request logic to the `app.py` workflow!
