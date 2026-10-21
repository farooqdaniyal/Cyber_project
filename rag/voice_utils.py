import io
import os

from gtts import gTTS
from groq import Groq
from langchain_groq import ChatGroq


def text_to_speech(text: str, lang: str = "en") -> bytes:
    """Text ko MP3 bytes me convert karta hai (gTTS)."""
    buf = io.BytesIO()
    gTTS(text=text[:3000], lang=lang).write_to_fp(buf)
    return buf.getvalue()


def speech_to_text(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Audio bytes ko Groq Whisper se text me convert karta hai."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    result = client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model="whisper-large-v3-turbo",
        response_format="text",
    )
    return result if isinstance(result, str) else result.text


def answer_from_report(report: str, question: str) -> str:
    """Sirf incident report ke basis par jawab deta hai."""
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    prompt = (
        "You are a SOC assistant. Answer the analyst's question using ONLY the "
        "incident report below. If the answer is not in the report, say so. "
        "Keep it under 4 sentences. No action has been executed; steps are "
        "recommendations only.\n\n"
        f"REPORT:\n{report}\n\nQUESTION: {question}"
    )
    return llm.invoke(prompt).content