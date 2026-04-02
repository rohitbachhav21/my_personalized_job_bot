import re

# Skip opening detail tab for obvious non-tech titles (saves time on fresher/intern SERPs).
TITLE_SKIP_PHRASES = [
    "telecaller",
    "tele-caller",
    "delivery executive",
    "delivery boy",
    "field sales",
    "sales officer",
    "counter sales",
    "store manager",
    "security guard",
    "housekeeping",
    "driver ",
    "office boy",
    "peon",
    "receptionist",
    "data entry operator",
    "collection officer",
    "loan officer",
    "mis",
    "hr",
    "recruiter",
    "accountant",
    "taxation",
    "audit",
    "financial manager",
    "financial controller",
    "financial advisor",
    
]


def should_skip_job_by_title(title):
    if not title:
        return False
    t = title.lower()
    return any(p in t for p in TITLE_SKIP_PHRASES)


def valid_experience(text):

    text = text.lower()

    fresher_keywords = [
        "fresher",
        "intern",
        "internship",
        "trainee",
        "entry level",
        "junior"
    ]

    for word in fresher_keywords:
        if word in text:
            return True

    ranges = re.findall(r'(\d+)\s*[-–]\s*(\d+)\s*(?:years|year|yrs|yr)', text)

    for r in ranges:
        if int(r[0]) > 2:
            return False

    plus_exp = re.findall(r'(\d+)\+\s*(?:years|year|yrs|yr)', text)

    for p in plus_exp:
        if int(p) > 2:
            return False

    return True


def valid_technology(text, technologies, quiet=False):
    """
    Match stack skills using whole phrases / word boundaries.
    Caller should pass job-description text only (Key skills strip handled upstream).
    """
    if not (text or "").strip():
        return False

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    reject_roles = [
        "bpo", "voice process", "non voice", "call center",
        "customer support", "telecaller", "sales", "marketing",
        "hr", "recruiter", "mis", "data entry", "accountant",
    ]

    for r in reject_roles:
        if re.search(rf"\b{re.escape(r)}\b", text):
            return False

    matched = []

    for tech in technologies:
        tech_clean = re.sub(r"[^\w\s]", " ", tech.lower()).strip()
        parts = tech_clean.split()
        if not parts:
            continue
        pattern = r"\b" + r"\s+".join(re.escape(p) for p in parts) + r"\b"
        if re.search(pattern, text):
            matched.append(tech)
            if not quiet:
                print("Matched technology:", tech)

    if quiet and matched:
        print("Skill match (JD):", ", ".join(matched[:8]) + ("…" if len(matched) > 8 else ""))

    return len(matched) >= 1