# ============================================================
# STEP 3: LLM Integration
# Combines ML Detection result + RAG retrieved policy into
# a clear, professional incident report using Gemini LLM.
# Run this in the same "rag" folder (needs chroma_security_db
# from Step 2 to already exist).
# ============================================================

import os
from dotenv import load_dotenv
load_dotenv()

# from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

# ---------- Make file paths work no matter where this script is run from ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_security_db")

# ---------- STEP A: Reload the Existing ChromaDB (from Step 2) ----------
print("Loading existing ChromaDB...")

# Embeddings still use Gemini (Groq does not provide an embeddings API)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
# embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embeddings
)

retriever = vector_store.as_retriever(search_kwargs={"k": 2})

print("ChromaDB loaded successfully.")

# ---------- STEP B: Set Up the LLM (Groq instead of Gemini) ----------
# Groq's free tier has generous token limits and is usually much
# faster, with fewer "high demand" errors than Gemini.
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.3)

print("LLM ready (using Groq).")

# ---------- STEP C: Build the Prompt Template ----------
# This prompt tells the LLM exactly what role to play and what
# information it will receive (ML result + RAG policy context).

prompt = ChatPromptTemplate.from_template("""
You are a Cyber Security Analyst AI. You have been given the result of
an automated network traffic detection system, along with the relevant
company security policy retrieved for this type of incident.

Detection Result: {detection_result}

Relevant Security Policy (retrieved from company documents):
{policy_context}

Write a clear, professional incident summary report with the following
sections:
1. Incident Overview (what was detected)
2. Severity Assessment (based on the policy)
3. Recommended Response Steps (based on the policy, in your own words)
4. Escalation Note (who should be notified)

Keep the report concise and easy to read, as if writing for a manager
who is not a technical expert.
""")

# ---------- STEP D: Combine Everything Into One Function ----------

def generate_incident_report(detection_result: str):
    """
    Takes a detection result (e.g. 'DDoS ATTACK detected'),
    retrieves the relevant policy from RAG, and asks the LLM
    to generate a full incident report.
    """
    # Step 1: Retrieve relevant policy chunks from ChromaDB
    retrieved_docs = retriever.invoke(detection_result)
    policy_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # Step 2: Build the final prompt with both pieces of information
    final_prompt = prompt.format(
        detection_result=detection_result,
        policy_context=policy_context
    )

    # Step 3: Ask the LLM to generate the report
    response = llm.invoke(final_prompt)

    # Step 4: Extract clean text only.
    # Newer Gemini models return response.content as a list of
    # content blocks (with type/text/extras) instead of a plain
    # string, so we need to pull out just the "text" fields.
    if isinstance(response.content, str):
        return response.content
    elif isinstance(response.content, list):
        text_parts = []
        for block in response.content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)
        return "\n".join(text_parts)
    else:
        return str(response.content)

# ---------- STEP E: TEST IT ----------

print("\n" + "=" * 60)
print("TEST 1: DDoS Attack Detected")
print("=" * 60)
report_1 = generate_incident_report("DDoS ATTACK detected in network traffic")
print(report_1)

print("\n" + "=" * 60)
print("TEST 2: Heartbleed Attack Detected")
print("=" * 60)
report_2 = generate_incident_report("Heartbleed ATTACK detected in network traffic")
print(report_2)

print("\n" + "=" * 60)
print("LLM INTEGRATION TEST COMPLETE!")
print("If both reports above are clear, relevant, and well-structured,")
print("the LLM + RAG + ML pipeline is working correctly.")
print("=" * 60)