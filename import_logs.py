import os
import httpx
import tiktoken
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import streamlit as st

# Setup environment and network (matching main app)
os.environ["TIKTOKEN_CACHE_DIR"] = "./token"
client = httpx.Client(verify=False)

# Read credentials from Streamlit secrets file
try:
    # Manual extraction from the toml file since streamlit isn't fully running here
    
    base_url = secrets["GENAILAB_BASE_URL"]
    api_key = secrets["GENAILAB_API_KEY"]
except Exception:
    print("Error: Ensure .streamlit/secrets.toml is configured correctly.")
    exit(1)

# Initialize the exact same embedding model used by the main application
embedding_model = OpenAIEmbeddings(
    base_url=base_url,
    model="azure/genailab-maas-text-embedding-3-large",
    api_key=api_key,
    http_client=client
)

DB_DIR = os.getenv("DB_PATH", "./data/vector_index")
LOGS_DIR = "./existing_logs"

def batch_import_logs():
    if not os.path.exists(LOGS_DIR) or not os.listdir(LOGS_DIR):
        print(f"No logs found in '{LOGS_DIR}'. Please drop your log files there.")
        return

    # Load existing database matrix or build a new one
    vectordb = Chroma(persist_directory=DB_DIR, embedding_function=embedding_model)
    documents_to_add = []

    print(f"Scanning '{LOGS_DIR}' for historical logs...")
    
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".log") or filename.endswith(".txt"):
            file_path = os.path.join(LOGS_DIR, filename)
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                # Grab the last 100 lines where error/crash data typically aggregates
                tail_log = "".join(lines[-100:])
            
            # Format the metadata block so the RAG engine understands it later
            formatted_content = f"""
            Historical Log Filename: {filename}
            Log Error Snippet:
            ---
            {tail_log}
            ---
            Verified Status: Evaluated historical system failure payload.
            """
            
            doc = Document(
                page_content=formatted_content,
                metadata={"source_file": filename, "type": "historical_import"}
            )
            documents_to_add.append(doc)
            print(f"-> Prepared: {filename} ({len(lines)} lines parsed)")

    if documents_to_add:
        print(f"\nEmbedding and injecting {len(documents_to_add)} documents into Chroma memory...")
        vectordb.add_documents(documents_to_add)
        print("Success! Your historical logs are now indexed into the application's memory.")
    else:
        print("No valid log data found to import.")

if __name__ == "__main__":
    # Ensure you install toml if not already present: pip install toml
    batch_import_logs()