# app/scam_detector.py
import re
from app.rag import client, groq_client

RULES = [

        {
        "id": "authority_endorsement",
        "description": "Claims endorsement by an unnamed or vague authority figure to build false credibility",
        "weight": 20,
        "patterns": [
            r"(recommended|endorsed) by.{0,25}(top|leading|renowned|respected).{0,25}(executive|banker|official|expert)",
            r"personally (recommend|invite)"
        ]
    },
    {
        "id": "informal_deposit_channel",
        "description": "Directs you to deposit money or register through an informal group admin rather than an official channel",
        "weight": 25,
        "patterns": [
            r"(whatsapp|telegram) group admin",
            r"message.{0,20}admin.{0,20}(register|deposit|join)",
            r"consistent.{0,15}(weekly|daily|monthly).{0,15}payout"
        ]
    },


    {
        "id": "upfront_payment",
        "description": "Asks for an upfront payment or fee before you receive a job, prize, or return",
        "weight": 30,
        "patterns": [
            r"registration fee", r"training fee", r"processing fee", r"activation fee",
            r"caution fee", r"logistics fee", r"clearance fee", r"verification fee",
            r"pay.{0,15}(before|to (start|secure|unlock|access))",
            r"send.{0,15}(money|cash|fee).{0,15}(to start|to secure|first)",
            r"once and for all"
        ]
    },
    {
        "id": "unrealistic_returns",
        "description": "Promises unusually high, guaranteed, or risk-free returns",
        "weight": 30,
        "patterns": [
            r"guaranteed.{0,20}(return|profit|income)",
            r"(double|triple|multiply).{0,20}(your )?(money|investments?|capital|funds?)",
            r"risk[- ]free",
            r"\b\d{1,3}\s?%.{0,20}(return|profit|roi|daily|weekly|monthly)",
            r"(daily|weekly) profit",
            r"no risk"
        ]
    },
    {
        "id": "urgency_pressure",
        "description": "Uses urgency or pressure to push a fast decision",
        "weight": 15,
        "patterns": [
            r"act now", r"limited slots?", r"offer expires", r"only today",
            r"last chance", r"hurry", r"few slots left", r"before it'?s too late",
            r"closing soon", r"urgent(ly)?"
        ]
    },
    {
        "id": "unverifiable_contact",
        "description": "Only reachable via WhatsApp/Telegram with no verifiable address or website",
        "weight": 15,
        "patterns": [
            r"whatsapp only", r"contact.{0,10}via whatsapp", r"no office visit",
            r"dm to apply", r"telegram only", r"message me directly"
        ]
    },
    {
        "id": "requests_sensitive_info",
        "description": "Asks for your BVN, NIN, OTP, PIN, or bank login details",
        "weight": 35,
        "patterns": [
            r"send.{0,10}(your )?(bvn|otp|nin|pin)", r"one[- ]time password",
            r"bank login", r"your password", r"atm pin"
        ]
    },
    {
        "id": "too_good_reward",
        "description": "Price or reward is dramatically disproportionate to what's normal",
        "weight": 20,
        "patterns": [
            r"brand new iphone.{0,20}(cheap|giveaway)", r"clearance (sale|price)",
            r"give ?away price", r"custom cleared cheap",
            r"you (have|'ve) won", r"claim your prize", r"lottery winner"
        ]
    },
    {
        "id": "impersonation",
        "description": "Claims to be a bank, government agency, or known company via an unofficial channel",
        "weight": 30,
        "patterns": [
            r"central bank of nigeria", r"\befcc\b", r"\bfirs\b",
            r"bvn will be blocked", r"cbn directive", r"account will be (blocked|suspended)",
            r"nin will be deactivated"
        ]
    },
    {
        "id": "disproportionate_offer",
        "description": "A large payout is offered in exchange for a smaller upfront payment",
        "weight": 25,
        "patterns": [
            r"\d[\d,]*\s?(k|thousand|million|naira|ngn).{0,30}if you (can |will )?pay",
            r"pay.{0,20}\d[\d,]*\s?(k|thousand|naira).{0,20}(once|now|first)"
        ]
    },
]

SEMANTIC_POINTS = {"NONE": 0, "LOW": 20, "MEDIUM": 50, "HIGH": 85}

def pattern_check(text):
    text_lower = text.lower()
    matched = []
    total_score = 0
    for rule in RULES:
        if any(re.search(pattern, text_lower) for pattern in rule["patterns"]):
            matched.append(rule)
            total_score += rule["weight"]
    return min(total_score, 100), matched

def semantic_check(text):
    prompt = f"""You are a fraud-pattern analyst. Assess ONLY the manipulation tactics used in this message, not whether any named company is legitimate. Message: "{text}"

If this is an ordinary, professional message — a standard job posting, business communication, or greeting — with no manipulative framing, respond NONE. Only flag LOW, MEDIUM, or HIGH when you observe specific tactics like unrealistic returns, artificial urgency, unverified authority claims, or pressure to bypass normal verification.

Respond in exactly this format:
SEMANTIC_RISK: [NONE, LOW, MEDIUM, or HIGH]
REASONING: [one or two plain sentences on manipulation tactics observed, e.g. unrealistic returns, urgency, disproportionate reward. If none, say so.]"""
    try:
        response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        raw = response.text
    except Exception:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = completion.choices[0].message.content

    risk_match = re.search(r"SEMANTIC_RISK:\s*(NONE|LOW|MEDIUM|HIGH)", raw, re.IGNORECASE)
    reasoning_match = re.search(r"REASONING:\s*(.+)", raw, re.DOTALL)
    semantic_risk = risk_match.group(1).upper() if risk_match else "NONE"
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "No additional concerns noted."
    return semantic_risk, reasoning

def check_text(text):
    pattern_score, matched_rules = pattern_check(text)
    semantic_risk, reasoning = semantic_check(text)
    semantic_score = SEMANTIC_POINTS.get(semantic_risk, 0)
    final_score = max(pattern_score, semantic_score)

    if final_score >= 70:
        risk_level = "HIGH RISK"
    elif final_score >= 35:
        risk_level = "MEDIUM RISK"
    elif final_score > 0:
        risk_level = "LOW RISK"
    else:
        risk_level = "NO OBVIOUS RED FLAGS"

    return {
        "score": final_score,
        "risk_level": risk_level,
        "matched_rules": matched_rules,
        "semantic_risk": semantic_risk,
        "semantic_reasoning": reasoning
    }