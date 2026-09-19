# app/scam_detector.py

RULES = [
    {
        "id": "upfront_payment",
        "description": "Asks for an upfront payment, registration fee, or training fee before you start work or receive returns",
        "weight": 30,
        "keywords": ["registration fee", "training fee", "processing fee", "pay before",
                     "send money to start", "activation fee", "caution fee", "logistics fee",
                     "pay to secure", "clearance fee"]
    },
    {
        "id": "unrealistic_returns",
        "description": "Promises unusually high, guaranteed, or risk-free returns",
        "weight": 25,
        "keywords": ["guaranteed return", "double your money", "100% profit", "risk-free investment",
                     "triple your money", "no risk", "guaranteed profit", "% roi", "daily profit",
                     "weekly profit", "guaranteed income"]
    },
    {
        "id": "urgency_pressure",
        "description": "Uses urgency or fear tactics to push a fast decision",
        "weight": 15,
        "keywords": ["act now", "limited slots", "offer expires", "only today", "last chance",
                     "hurry", "few slots left", "before it's too late", "closing soon", "urgent"]
    },
    {
        "id": "unverifiable_contact",
        "description": "Only reachable via WhatsApp/Telegram with no verifiable company address or website",
        "weight": 20,
        "keywords": ["whatsapp only", "contact via whatsapp", "no office visit", "dm to apply",
                     "telegram only", "message me directly"]
    },
    {
        "id": "requests_sensitive_info",
        "description": "Asks for your BVN, NIN, OTP, PIN, or bank login details",
        "weight": 35,
        "keywords": ["send your bvn", "send your otp", "your pin", "your nin number", "atm pin",
                     "bank login", "one time password", "send otp", "your password"]
    },
    {
        "id": "too_good_price",
        "description": "Price is dramatically below normal market value",
        "weight": 20,
        "keywords": ["brand new iphone", "clearance sale", "swap deal", "custom cleared cheap",
                     "give away price", "clearance price"]
    },
    {
        "id": "impersonation",
        "description": "Claims to be from a bank, government agency, or well-known company via an unofficial channel",
        "weight": 30,
        "keywords": ["central bank of nigeria", "efcc", "firs", "your bvn will be blocked",
                     "cbn directive", "your account will be blocked", "nin will be deactivated",
                     "your account has been suspended"]
    },
]

def check_text(text):
    text_lower = text.lower()
    matched = []
    total_score = 0

    for rule in RULES:
        if any(keyword in text_lower for keyword in rule["keywords"]):
            matched.append(rule)
            total_score += rule["weight"]

    total_score = min(total_score, 100)

    if total_score >= 70:
        risk_level = "HIGH RISK"
    elif total_score >= 35:
        risk_level = "MEDIUM RISK"
    elif total_score > 0:
        risk_level = "LOW RISK"
    else:
        risk_level = "NO OBVIOUS RED FLAGS DETECTED"

    return {
        "score": total_score,
        "risk_level": risk_level,
        "matched_rules": matched
    }