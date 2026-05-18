# LangChain imports
import streamlit as st
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_community.document_loaders import RSSFeedLoader

# ====================== CONFIG ======================
st.set_page_config(page_title="OverSiteSentry AI", layout="wide")
st.title("🔒 OverSiteSentry AI - Dynamic Top 30 + Vulnerability Catalog")

# === GOOGLE API KEY (add in Streamlit secrets or environment) ===
google_api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    st.error("🚨 Please add your GOOGLE_API_KEY in Streamlit secrets or as environment variable.")
    st.stop()

# ====================== YOUR TOP FEEDS ======================
DEFAULT_TOP_FEEDS = [
    "https://thehackernews.com/feed",
    "https://darkreading.com/rss.xml",
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://blogs.jpcert.or.jp/en/atom.xml",
    "https://cert.pl/en/atom.xml",
    "https://www.cert.ssi.gouv.fr/feed/",
    "https://cert.be/en/rss",
    "https://cert.europa.eu/publications/threat-intelligence-rss",
    "https://cert.gov.ua/api/articles/rss",
    "http://www.reddit.com/r/blueteamsec/.rss",
    "http://www.reddit.com/r/netsec/.rss"
]


if st.button("Run AI Update Now"):
    # LangChain agent logic here:
    # 1. Load feeds

  
    # 2. LLM summarizes + extracts vulns
    # 3. Add to Chroma vectorstore
    # 4. Re-rank Top 30 if needed
    st.success("Catalog updated!")

# Display searchable catalog
query = st.text_input("Search vulnerabilities or news...")
if query:
    # RAG search on your catalog
    results = vectorstore.similarity_search(query)

  st.write(results)
