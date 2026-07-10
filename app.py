import streamlit as st
import requests
import sqlite3
from datetime import datetime

# ==========================================
# 1. Database Setup & Functions
# ==========================================
DB_NAME = "triage_history.db"

def init_db():
    """Creates the local database and table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bug_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            error_message TEXT,
            actions_taken TEXT,
            log_snippet TEXT,
            ai_resolution TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_triage_record(error_message, actions_taken, log_snippet, ai_resolution):
    """Saves the completed triage report to the local database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bug_reports (timestamp, error_message, actions_taken, log_snippet, ai_resolution)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_message, actions_taken, log_snippet, ai_resolution))
    conn.commit()
    conn.close()

def search_similar_errors(search_term):
    """Searches the database for similar historical errors using the first keyword."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT error_message, ai_resolution FROM bug_reports 
        WHERE error_message LIKE ? OR log_snippet LIKE ?
        ORDER BY timestamp DESC LIMIT 3
    ''', (f'%{search_term}%', f'%{search_term}%'))
    results = cursor.fetchall()
    conn.close()
    return results

# Initialize the DB when the app starts
init_db()

# ==========================================
# 2. Page Configuration & UI
# ==========================================
st.set_page_config(page_title="AI Maintenance Assistant", layout="wide")
st.title("🔧 Automated Bug Triage & Troubleshooting Assistant")

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    try:
        # Construct the proper v1 endpoint using secrets file keys
        api_url = os.getenv("API_ENDPOINT", "https://api.your-service.com/v1") if "GENAILAB_BASE_URL" in st.secrets else st.secrets["GENAILAB_API_URL"]
        api_key = st.secrets["GENAILAB_API_KEY"]
        st.success("API Credentials loaded from secrets.")
    except Exception:
        api_url = st.text_input("Gateway Endpoint", value="https://genailab.tcs.in/v1/chat/completions")
        api_key = st.text_input("API Key / Bearer Token", type="password")
    
    max_log_lines = st.slider("Max Log Lines to Parse", min_value=10, max_value=200, value=50)
    
    st.divider()
    st.subheader("Database Stats")
    conn = sqlite3.connect(DB_NAME)
    count = conn.cursor().execute('SELECT COUNT(*) FROM bug_reports').fetchone()[0]
    conn.close()
    st.metric("Total Historical Records", count)

    # === Add this under your st.metric("Total Historical Records", count) line ===
    st.divider()
    st.subheader("📚 Saved Incidents History")
    
    # Fetch all records to display summary titles in the sidebar
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, error_message, ai_resolution FROM bug_reports ORDER BY timestamp DESC')
    all_history = cursor.fetchall()
    conn.close()
    
    if all_history:
        for timestamp, err_msg, resolution in all_history:
            # Crop the error string so it fits neatly in the sidebar menu
            short_err = err_msg[:30] + "..." if len(err_msg) > 30 else err_msg
            
            # Create a collapsible drawer for every single past incident record
            with st.sidebar.expander(f"🕒 {timestamp} | {short_err}"):
                st.caption(f"**Full Error:** {err_msg}")
                st.markdown("**🧠 Past AI Resolution Provided:**")
                st.info(resolution)
    else:
        st.caption("No historical records captured yet.")


# Main Interface Layout Splitting
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Issue Context Capture")
    error_message = st.text_input("Error Message / Exception", placeholder="e.g., NullPointerException at DatabaseConnection.java:42")
    actions_taken = st.text_area("Actions Taken", placeholder="Describe what steps the user performed...", height=150)
    uploaded_file = st.file_uploader("Attach Log File (.txt, .log)", type=["txt", "log"])

# Log File Processing Logic
processed_log_content = ""
if uploaded_file is not None:
    lines = uploaded_file.getvalue().decode("utf-8").splitlines()
    trimmed_lines = lines[-max_log_lines:]
    processed_log_content = "\n".join(trimmed_lines)
    st.success(f"Processed the latest {len(trimmed_lines)} lines of the log file.")
    with st.expander("View Filtered Log Snippet"):
        st.code(processed_log_content, language="log")

# ==========================================
# 3. AI Communication & Database Integration
# ==========================================
with col2:
    st.subheader("AI Analysis & Troubleshooting")
    
    # Initialize session state storage bucket so output survives the sidebar rerun refresh
    if "current_analysis" not in st.session_state:
        st.session_state.current_analysis = None

    if st.button("Analyze Issue", type="primary"):
        if not api_key or not error_message:
            st.error("Please provide both the API Key and an Error Message.")
        else:
            with st.spinner("Searching historical database and analyzing logs..."):
                historical_context = ""
                # Parse using the first word/module token to pull general error types from SQLite match pool
                search_token = error_message.split()[0] if error_message.split() else ""
                past_errors = search_similar_errors(search_token)
                
                if past_errors:
                    historical_context = "HISTORICAL MATCHES FOUND:\n"
                    for error, resolution in past_errors:
                        historical_context += f"- Past Error: {error}\n  Resolution Used: {resolution}\n\n"
                
                system_instruction = "You are an advanced application support engineering assistant."
                user_payload = f"""
                PRIMARY ERROR: {error_message}
                ACTIONS TAKEN BY USER: {actions_taken}
                
                {historical_context}
                
                FILTERED SYSTEM LOG SNIPPET:
                ---
                {processed_log_content if processed_log_content else "No log attached."}
                ---
                
                Please provide your analysis:
                1. Root Cause Hypothesis
                2. Recommended Troubleshooting Steps
                """
                
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                data = {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_payload}
                    ],
                    "temperature": 0.2
                }
                
                try:
                    # Bypassing corporate internal proxy/SSL cert checks with verify=False
                    response = requests.post(api_url, headers=headers, json=data, timeout=30, verify=False)
                    
                    if response.status_code == 200:
                        ai_response = response.json()['choices'][0]['message']['content']
                        
                        # Cache target strings safely inside active context state
                        st.session_state.current_analysis = ai_response
                        
                        # Save historical logs payload record to DB
                        save_triage_record(error_message, actions_taken, processed_log_content, ai_response)
                        
                        # Force refresh to capture updated historical records count indicator block inside sidebar panel
                        st.rerun()
                        
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                        
                except Exception as e:
                    st.error(f"Failed to connect: {str(e)}")

    # Securely render assessment results without breaking scope workflows
    if st.session_state.current_analysis:
        st.markdown("### 📋 Triage Assessment")
        st.markdown(st.session_state.current_analysis)
        st.success("Analysis saved to local database for future reference.")