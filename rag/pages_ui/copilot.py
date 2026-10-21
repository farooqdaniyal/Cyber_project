import hashlib

import streamlit as st

import assistant
import briefing
import theme
from data_utils import last_report

try:                                   # tumhari purani voice_utils: Whisper (speech->text) aur LLM jawab
    from voice_utils import speech_to_text, answer_from_report
    VOICE_OK, VOICE_ERR = True, ""
except Exception as _e:                # gTTS / key / package missing
    VOICE_OK, VOICE_ERR = False, str(_e)

AVATARS = {"user": ":material/person:", "assistant": ":material/smart_toy:"}

SUGGESTIONS = [
    "How many cases are pending?",
    "Which asset is attacked the most?",
    "What are the most common attacks?",
    "Summarize the latest attack",
]


def _answer(question, ctx):
    quick = assistant.quick_answer(question, ctx)
    if quick:
        return quick, "Answered directly from the audit data"
    if not VOICE_OK:
        return ("I can answer questions about pending cases, targeted assets, attack types and the latest attacks. "
                "Open-ended questions need the language-model module, which is not available right now."), "data only"
    try:
        return answer_from_report(assistant.facts_text(ctx, last_report()), question), "Answered by the LLM using your audit data"
    except Exception as e:
        return f"Sorry, I could not reach the language model ({e}).", "error"


def _ask(question, spoken, ctx):
    history = st.session_state.setdefault("copilot_chat", [])
    history.append({"role": "user", "content": question, "mic": spoken})
    answer, source = _answer(question, ctx)
    audio = None
    if spoken or st.session_state.get("cp_speak"):
        audio, _ = briefing.synthesize(assistant.speakable(answer))
    history.append({"role": "assistant", "content": answer, "source": source, "audio": audio, "fresh": audio is not None})


def render():
    theme.page_header("AI Assistant", "AI Assistant",
                      "Ask questions about your SOC data by typing or by using your voice.")
    ctx = assistant.load_context()
    history = st.session_state.setdefault("copilot_chat", [])
    st.session_state.setdefault("cp_mic_n", 0)

    n_rec = 0 if ctx is None else len(ctx["d"])
    has_rep = bool(last_report())
    st.markdown(
        f'<div class="status-banner status-info" style="margin-top:0"><strong>Data sources:</strong> audit log '
        f'({n_rec} records){" + latest incident report" if has_rep else ""}. Answers come only from this data.</div>',
        unsafe_allow_html=True)

    # ---- voice question ----
    with st.container(border=True):
        st.markdown('<div class="card-title">Ask with your voice</div>'
                    '<div style="color:#8c9ac4;font-size:.76rem;margin:-.15rem 0 .5rem">'
                    'Click the mic, ask your question, then click stop. The answer appears as text and is also read aloud.</div>',
                    unsafe_allow_html=True)
        pending_q = None
        if hasattr(st, "audio_input") and VOICE_OK:
            mic = st.audio_input("Record your question", key=f"cp_mic_{st.session_state['cp_mic_n']}",
                                 label_visibility="collapsed")
            if mic is not None:
                data = mic.getvalue()
                with st.spinner("Transcribing your question..."):
                    try:
                        text = (speech_to_text(data) or "").strip()
                    except Exception as e:
                        text = ""
                        st.error(f"Could not transcribe: {e}")
                if text:
                    _ask(text, True, ctx)
                st.session_state["cp_mic_n"] += 1       # recorder khali karo
                st.rerun()
        elif not VOICE_OK:
            st.caption(f"Voice is not available right now ({VOICE_ERR[:80]}). You can still type your questions.")
        else:
            st.caption("This Streamlit version has no microphone recorder. Please type your question.")

        cols = st.columns(len(SUGGESTIONS))
        for c, s in zip(cols, SUGGESTIONS):
            if c.button(s, key=f"cp_sug_{s}", use_container_width=True):
                pending_q = s

    top = st.columns([4, 1.3, 1])
    top[0].caption("Tip: simple questions like 'How many cases are pending?' are answered directly from the data, without the LLM.")
    st.session_state["cp_speak"] = top[1].toggle("Read answers aloud", value=st.session_state.get("cp_speak", False), key="cp_speak_t")
    if top[2].button("Clear chat", key="cp_clear", use_container_width=True):
        st.session_state["copilot_chat"] = []
        st.rerun()

    # ---- chat history ----
    for m in history:
        with st.chat_message(m["role"], avatar=AVATARS[m["role"]]):
            if m.get("mic"):
                st.caption("Asked by voice")
            st.markdown(m["content"])
            if m["role"] == "assistant":
                if m.get("source"):
                    st.caption(m["source"])
                if m.get("audio"):
                    autoplay = m.pop("fresh", False)
                    try:
                        st.audio(m["audio"], format="audio/mp3", autoplay=autoplay)
                    except TypeError:
                        st.audio(m["audio"], format="audio/mp3")

    # chat input neeche chipka rehta hai: aakhri jawab (aur audio player) uske peeche na chhupe
    st.markdown('<div style="height:110px"></div>', unsafe_allow_html=True)

    q = st.chat_input("Type your question...") or pending_q
    if q:
        with st.spinner("Thinking..."):
            _ask(q, False, ctx)
        st.rerun()