"""
Shift Briefing: audit data se ~20 second ka summary banata hai (LLM ke baghair, seedhi template se)
aur gTTS se awaaz mein badalta hai. Har number asli data se aata hai.
"""
import io

import pandas as pd


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def fmt_age(delta: pd.Timedelta) -> str:
    mins = max(int(delta.total_seconds() // 60), 0)
    if mins < 90:
        return _plural(max(mins, 1), "minute")
    hours = mins // 60
    if hours < 48:
        return _plural(hours, "hour")
    return _plural(hours // 24, "day")


def build(name, now, pend_n, pend_crit, oldest_ts, asset, asset_n, scope, attack, attack_n):
    """Returns dict(text=..., speech=...). text screen ke liye, speech awaaz ke liye."""
    name = name.capitalize() if name.islower() else name
    part = "morning" if now.hour < 12 else "afternoon" if now.hour < 18 else "evening"
    clock = now.strftime("%I:%M %p").lstrip("0")
    parts = [f"Good {part}, {name}."]

    if pend_n:
        verb = "is" if pend_n == 1 else "are"
        parts.append(f"As of {clock}, {_plural(pend_n, 'case')} {verb} awaiting analyst review, "
                     f"{pend_crit} of them critical.")
    else:
        parts.append(f"As of {clock}, no cases are awaiting analyst review.")

    if asset:
        parts.append(f"The most targeted asset {scope} is the {asset}, with {_plural(int(asset_n), 'attack')}.")
    if attack:
        parts.append(f"The most common attack is {attack}, with {_plural(int(attack_n), 'detection')}.")
    if oldest_ts is not None and pd.notna(oldest_ts):
        parts.append(f"The oldest pending case has been waiting for {fmt_age(pd.Timestamp(now) - pd.Timestamp(oldest_ts))}.")

    if pend_crit:
        parts.append("Please review the critical cases first.")
    elif pend_n:
        parts.append("Please review the pending cases.")
    else:
        parts.append("Nothing urgent at the moment.")

    text = " ".join(parts)
    speech = text.replace(" / ", " and ").replace("/", " ")
    return {"text": text, "speech": speech}


def synthesize(text: str):
    """Returns (mp3_bytes | None, error | None). Internet ya gTTS na ho to text phir bhi dikhta hai."""
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text, lang="en").write_to_fp(buf)
        return buf.getvalue(), None
    except Exception as e:          # no internet / gTTS not installed
        return None, str(e)