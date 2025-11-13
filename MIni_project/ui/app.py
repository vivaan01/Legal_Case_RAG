import os
import time
import requests
import streamlit as st

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Check backend health
def check_backend():
    try:
        response = requests.get(f"{BACKEND}/", timeout=5)
        return response.ok
    except:
        return False

if not check_backend():
    st.error("Backend server is not responding. Please ensure it's running and try again.")
    st.stop()

st.set_page_config(page_title="Legal Case RAG", page_icon="⚖️", layout="wide")
st.title("⚖️ Legal Case RAG — Adaptive + Tool-Enriched (Ollama)")

with st.sidebar:
	st.header("Ingest PDFs")
	uploaded = st.file_uploader("Upload legal ruling PDF", type=["pdf"], accept_multiple_files=True)
	if st.button("Ingest"):
		if not uploaded:
			st.warning("Upload at least one PDF.")
		else:
			for file in uploaded:
				files = {"file": (file.name, file.getvalue(), "application/pdf")}
				with st.spinner(f"Ingesting {file.name} ..."):
					r = requests.post(f"{BACKEND}/ingest", files=files, timeout=300)
					if r.ok:
						st.success(f"{file.name} -> {r.json()}")
					else:
						st.error(f"Failed: {r.text}")

st.subheader("Search Cases")
query = st.text_input("Your question", placeholder="e.g., Breach damages in contract disputes?")
col1, col2 = st.columns([1, 1])
with col1:
	stream = st.checkbox("Stream response", value=True)
with col2:
	user_id = st.text_input("User ID", value="default_user")

if st.button("Search") and query.strip():
	if stream:
		placeholder = st.empty()
		accum = ""
		try:
			with requests.get(f"{BACKEND}/query_stream", params={"query": query, "user_id": user_id}, stream=True, timeout=300) as r:
				r.raise_for_status()
				for chunk in r.iter_content(chunk_size=None):
					if chunk:
						accum += chunk.decode("utf-8", errors="ignore")
						placeholder.markdown(accum)
			st.session_state["last_answer"] = accum
		except Exception as e:
			st.error(str(e))
	else:
		r = requests.post(f"{BACKEND}/query", json={"query": query, "user_id": user_id}, timeout=300)
		if r.ok:
			data = r.json()
			st.write(data.get("answer", ""))
			st.session_state["last_answer"] = data.get("answer", "")
		else:
			st.error(r.text)

st.subheader("Rate the answer")
rating = st.slider("Rating (1-5)", 1, 5, 4)
if st.button("Submit Rating"):
	if "last_answer" not in st.session_state:
		st.warning("Ask a question first.")
	else:
		r = requests.post(f"{BACKEND}/feedback", json={"query": query, "rating": rating, "user_id": user_id}, timeout=300)
		if r.ok:
			data = r.json()
			if data.get("healed"):
				st.info("Low rating detected. Healed response:")
				st.write(data.get("answer", ""))
			else:
				st.success("Feedback recorded. Thank you!")
		else:
			st.error(r.text)


