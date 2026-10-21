# ============================================================
# RISK SCORING ENGINE
# Converts a detection (attack type + model confidence + affected
# asset) into a 0-100 risk score and a level:
#   None / Low / Medium / High / Critical
#
# This is a deterministic formula (no LLM involved), so the same
# input always gives the same score and every number can be
# explained to a reviewer.
#
# Place this file in your "rag" folder.
# ============================================================

# ---------- Base severity per attack type (0-100) ----------
# Values follow the severity levels written in security_policy.txt:
#   Slowhttptest = Medium, Slowloris = Medium-High, GoldenEye/Hulk = High,
#   DDoS/Heartbleed = Critical
SEVERITY_BASE = {
    "BENIGN": 0,
    "DoS Slowhttptest": 40,
    "DoS slowloris": 45,
    "DoS GoldenEye": 60,
    "DoS Hulk": 65,
    "DDoS": 85,
    "Heartbleed": 95,
}

# ---------- How important the affected asset is ----------
# The same attack is more serious on a database than on a workstation.
ASSET_WEIGHT = {
    "Database Server": 1.25,
    "Domain Controller / DNS": 1.20,
    "Web Server": 1.00,
    "Employee Workstation": 0.75,
}

DEFAULT_ASSET = "Web Server"
UNKNOWN_ATTACK_BASE = 50  # used only if the model returns an unexpected class


def risk_level_from_score(score: float) -> str:
    """Map a 0-100 score to a level."""
    if score <= 0:
        return "None"
    if score < 25:
        return "Low"
    if score < 50:
        return "Medium"
    if score < 75:
        return "High"
    return "Critical"


def calculate_risk(prediction: str, confidence: float, asset: str = DEFAULT_ASSET) -> dict:
    """
    risk_score = attack_severity_base x model_confidence x asset_weight
    (capped at 100)

    Returns a dictionary with the score, the level, and a breakdown
    showing exactly how the score was calculated.
    """
    base = SEVERITY_BASE.get(prediction, UNKNOWN_ATTACK_BASE)
    weight = ASSET_WEIGHT.get(asset, 1.0)

    score = min(100.0, base * float(confidence) * weight)
    score = round(score, 1)
    level = risk_level_from_score(score)

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_breakdown": {
            "attack_type": prediction,
            "severity_base": base,
            "model_confidence": round(float(confidence), 4),
            "asset": asset,
            "asset_weight": weight,
        },
    }


if __name__ == "__main__":
    print("RISK ENGINE QUICK TEST\n")
    tests = [
        ("BENIGN", 1.00, "Web Server"),
        ("DoS Slowhttptest", 0.95, "Web Server"),
        ("DoS Hulk", 0.9994, "Web Server"),
        ("DoS Hulk", 0.9994, "Employee Workstation"),
        ("DoS Hulk", 0.9994, "Database Server"),
        ("DDoS", 1.00, "Web Server"),
        ("Heartbleed", 1.00, "Database Server"),
    ]
    for pred, conf, asset in tests:
        r = calculate_risk(pred, conf, asset)
        print(f"{pred:<18} conf={conf:<7} asset={asset:<24} -> {r['risk_score']:>5} ({r['risk_level']})")