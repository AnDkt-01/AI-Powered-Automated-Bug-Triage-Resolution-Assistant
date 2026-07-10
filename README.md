
****To run this, you will need an OpenAI API key (or similar) and a local Vector store.***

**To run this application, the following dependencies are required.**
  streamlit: For the web application interface.
  langchain & langchain-openai: For RAG and embedding orchestration.
  chromadb: For local vector storage.
  httpx: For secure API communication.
  sqlite3: Included in standard Python for local database management.
  toml: For secure configuration management.



The application follows a modular, decoupled architecture to ensure separation of concerns:
    Frontend: Built with Streamlit for a responsive, interactive user interface.
    Retrieval Layer (RAG): Uses a Chroma Vector Database for semantic search of historical log patterns.
    Intelligence Layer: Integrates via API with large language models to process log contexts and generate diagnostic hypotheses.
    Storage Layer: Utilizes a local SQLite relational database for structured incident history, audit trails, and metadata storage.
    Orchestration: Python-based services manage data ingestion, vector embedding, and prompt engineering guardrails to prevent model hallucinations.

Intellectual Property: This tool is provided as a reference implementation for automated triage workflows. It does not contain proprietary code, client-specific configurations, or confidential business logic.
Security & Compliance: This repository does not contain API keys, infrastructure credentials, or internal network paths. Users are responsible for providing their own API keys and ensuring the implementation meets their organizational security standards.
AI Hallucination: While the system utilizes prompt engineering and temperature constraints (set to 0.0) to minimize factual errors, it is an assistant tool. All AI-generated diagnostic outputs should be verified by qualified engineering personnel before taking corrective infrastructure actions.
Data Privacy: Users must ensure that no PII (Personally Identifiable Information) or sensitive client data is submitted to the application or included in the log files processed by the AI model.
