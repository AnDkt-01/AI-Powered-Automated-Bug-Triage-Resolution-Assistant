import httpx
from langchain_openai import ChatOpenAI
import toml

print("🔄 Loading configurations from secrets.toml...")
try:
    secrets = toml.load(".streamlit/secrets.toml")
    base_url = secrets["GENAILAB_BASE_URL"]
    api_key = secrets["GENAILAB_API_KEY"]
    print("✅ Secrets loaded successfully.")
except Exception as e:
    print(f"❌ Error loading secrets: {e}")
    print("Please ensure '.streamlit/secrets.toml' exists and contains your credentials.")
    exit(1)

print("\n🔄 Initializing HTTP client (bypassing SSL verification)...")
client = httpx.Client(verify=False)

print("🔄 Initializing GPT-4o-Mini model instance...")
llm = ChatOpenAI(
    base_url=base_url,
    model="azure/genailab-maas-gpt-4o-mini",
    api_key=api_key,
    http_client=client,
    temperature=0.2
)

print("\n📡 Sending test request to genailab.tcs.in...")
try:
    # Send a lightweight query to test network loop
    response = llm.invoke("Respond with exactly the word: SUCCESS")
    print("\n🎉 CONNECTION SUCCESSFUL!")
    print(f"AI Response: {response}")
except Exception as e:
    print("\n❌ CONNECTION FAILED!")
    print(f"Error Details: {str(e)}")