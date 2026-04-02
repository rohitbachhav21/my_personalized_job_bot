"""
Helpers to use Naukri job *description* (not Key skills / footer noise) for filtering
and a narrow slice of the page for saving locations.
"""

import re

from selenium.webdriver.common.by import By

KEY_SKILLS_MARKERS = [
    "key skills",
    "preferred skills",
    "preferred key skills",
    "technical skills",
    "skill highlights",
    "skills required",
    "must have skills",
    "role competencies",
]


def strip_key_skills_section(text: str) -> str:
    """Drop trailing 'Key skills' (and similar) blocks so tech matching uses JD prose only."""
    if not text:
        return ""
    lower = text.lower()
    cut = len(text)
    for m in KEY_SKILLS_MARKERS:
        for needle in (f"\n{m}\n", f"\n{m}:", f"\n{m} ", f" {m}\n"):
            idx = lower.find(needle)
            if idx != -1:
                cut = min(cut, idx)
        for pat in (
            rf"(?m)^\s*{re.escape(m)}\s*:?\s*$",
            rf"(?m)^\s*{re.escape(m)}\s*\n",
            rf"\n\s*{re.escape(m)}\s*:?\s*\n",
        ):
            match = re.search(pat, lower)
            if match:
                cut = min(cut, match.start())
    return text[:cut].strip()


def get_raw_job_description_text(driver) -> str:
    """Primary: 'Job description' section; fallback: main article (still strip key skills after)."""
    try:
        sec = driver.find_element(
            By.XPATH,
            "//section[contains(., 'Job description') or contains(., 'Job Description')]",
        )
        t = (sec.text or "").strip()
        if len(t) > 80:
            return t
    except Exception:
        pass
    try:
        art = driver.find_element(By.TAG_NAME, "article")
        t = (art.text or "").strip()
        if t:
            return t
    except Exception:
        pass
    return ""


def text_for_technology_matching(driver) -> str:
    """JD-only copy for skill match; excludes Key skills tail."""
    raw = get_raw_job_description_text(driver)
    return strip_key_skills_section(raw).lower()


def text_for_experience_check(driver) -> str:
    """Experience rules use full JD body (still from description/article, not whole site)."""
    raw = get_raw_job_description_text(driver)
    if raw:
        return raw.lower()
    try:
        return (driver.find_element(By.TAG_NAME, "body").text or "").lower()
    except Exception:
        return ""


def _location_pattern_from_phrase(phrase: str) -> str:
    clean = re.sub(r"[^\w\s]", " ", phrase.lower())
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return ""
    parts = clean.split()
    return r"\b" + r"\s+".join(re.escape(p) for p in parts) + r"\b"


def extract_locations(text: str, locations_list: list) -> str:
    """
    Cities only if they appear in the given text corpus (not whole HTML).
    Longer phrases first so 'work from home' beats shorter overlaps.
    """
    if not text or not locations_list:
        return "Not Specified"
    norm = re.sub(r"[^\w\s]", " ", text.lower())
    norm = re.sub(r"\s+", " ", norm)
    found = []
    for loc in sorted(locations_list, key=lambda x: len(x), reverse=True):
        pat = _location_pattern_from_phrase(loc)
        if not pat:
            continue
        if re.search(pat, norm):
            display = " ".join(w.capitalize() for w in loc.split()) if " " in loc else loc.title()
            found.append(display)
    seen = set()
    out = []
    for x in found:
        xl = x.lower()
        if xl not in seen:
            seen.add(xl)
            out.append(x)
    return ", ".join(sorted(out)) if out else "Not Specified"


def collect_location_corpus(driver) -> str:
    """
    Prefer visible job meta (links containing jobs-in-*, chip text) plus JD section —
    avoids 'recommended jobs' city lists in raw page_source.
    """
    chunks = []

    try:
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='jobs-in-']"):
            href = (a.get_attribute("href") or "").lower()
            m = re.search(r"jobs-in-([a-z0-9-]+)", href)
            if m:
                chunks.append(m.group(1).replace("-", " "))
            label = (a.text or "").strip()
            if label and len(label) < 60:
                chunks.append(label)
    except Exception:
        pass

    try:
        for el in driver.find_elements(
            By.CSS_SELECTOR,
            "[class*='location'], [class*='job-loc'], [data-testid*='location']",
        ):
            t = (el.text or "").strip()
            if t and len(t) < 120 and any(c.isalpha() for c in t):
                chunks.append(t)
    except Exception:
        pass

    raw_jd = get_raw_job_description_text(driver)
    if raw_jd:
        chunks.append(strip_key_skills_section(raw_jd)[:3500])

    return " \n ".join(chunks)
