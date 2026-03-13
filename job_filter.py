import re

import re

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


def valid_technology(text, technologies):

    text = text.lower()

    # normalize separators
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text.replace(",", " ")

    reject_roles = [
        "bpo",
        "voice process",
        "non voice",
        "call center",
        "customer support",
        "telecaller"
    ]

    for r in reject_roles:
        if r in text:
            return False

    for tech in technologies:
        if tech.lower() in text:
            print("Matched technology:", tech)
            return True

    return False