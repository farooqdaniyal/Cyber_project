# ============================================================
# STEP 2: RAG System (Security Policy Retrieval)
# Each PLAYBOOK = exactly ONE chunk, with playbook_id metadata.
# ============================================================

import os
import re
import shutil
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ---------- Paths ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILE = os.path.join(SCRIPT_DIR, "security_policy.txt")
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_security_db")

# ---------- STEP A: Load the Security Policy Document ----------
print("Loading security policy document...")
loader = TextLoader(POLICY_FILE, encoding="utf-8")
documents = loader.load()
print(f"Document loaded! Total characters: {len(documents[0].page_content)}")

# ---------- STEP B: Split manually (1 playbook = 1 chunk) ----------
raw_text = documents[0].page_content

# Split right before each "-----...\nPLAYBOOK" line
parts = re.split(r"\r?\n(?=-{20,}\r?\nPLAYBOOK )", raw_text)

chunks = []
for part in parts:
    m = re.search(r"PLAYBOOK\s+(\w+)\s*:", part)
    if not m:
        continue  # document header, skip
    chunks.append(
        Document(page_content=part.strip(), metadata={"playbook_id": m.group(1)})
    )

print(f"Document split into {len(chunks)} chunks")
for c in chunks:
    print("  ", c.metadata["playbook_id"], "->", c.page_content[:70].replace("\n", " "))

# ---------- STEP C: Embeddings ----------
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
print("Embeddings model ready")

# ---------- STEP D: Store in ChromaDB ----------
if os.path.exists(DB_DIR):
    shutil.rmtree(DB_DIR)
    print("Old database removed (fresh start).")

print("Storing chunks in ChromaDB... (this may take a moment)")
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_DIR
)
print("All chunks stored in ChromaDB!")
print("Database saved to folder: " + DB_DIR)

# ---------- STEP E: Retriever ----------
retriever = vector_store.as_retriever(search_kwargs={"k": 3})
print("\nRetriever ready! Running test queries now.\n")

# ---------- STEP F: Test queries ----------
def test_query(query_text):
    print("=" * 60)
    print(f"QUERY: {query_text}")
    print("=" * 60)
    results = retriever.invoke(query_text)
    for i, doc in enumerate(results, 1):
        print(f"\n--- Result {i} (playbook_id={doc.metadata.get('playbook_id')}) ---")
        print(doc.page_content[:300])
        print("...")
    print("\n")

test_query("What should be done if a DDoS attack occurs?")
test_query("Heartbleed vulnerability response steps")
test_query("What should be done for BENIGN normal traffic?")

# ---------- STEP G: Filter test ----------
print("=" * 60)
print("FILTER TEST: Slowhttptest must return playbook 03 (not DDoS)")
print("=" * 60)
filtered = vector_store.as_retriever(
    search_kwargs={"k": 1, "filter": {"playbook_id": "03"}}
)
res = filtered.invoke("DoS Slowhttptest ATTACK detected in network traffic")
for doc in res:
    print("playbook_id =", doc.metadata.get("playbook_id"))
    print(doc.page_content[:300])

print("=" * 60)
print("RAG SYSTEM TEST COMPLETE!")
print("Check: chunk list shows 01, 01b, 02, 03, 04, 05, 06")
print("Check: FILTER TEST shows playbook_id = 03")
print("=" * 60)