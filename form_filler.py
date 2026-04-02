import json
import os
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait


def load_form_config():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "form_answer.json")
    with open(path) as f:
        return json.load(f)


def _normalize(s):
    return (s or "").lower().strip()


def screening_ui_visible(driver):
    """True when an apply / screening layer is visible (modal, dialog, or focused form)."""
    try:
        if _find_screening_root(driver) is not None:
            return True
        for form in driver.find_elements(By.TAG_NAME, "form"):
            if not form.is_displayed():
                continue
            fields = form.find_elements(
                By.CSS_SELECTOR,
                "input:not([type='hidden']):not([type='search']):not([type='submit']), "
                "select, textarea",
            )
            if any(f.is_displayed() for f in fields):
                return True
        return False
    except Exception:
        return False


def wait_for_screening_ui(driver, timeout=12):
    def _visible(d):
        return screening_ui_visible(d)

    try:
        WebDriverWait(driver, timeout).until(_visible)
        return True
    except TimeoutException:
        return False


def _find_screening_root(driver):
    """
    Prefer a single modal/dialog container so we do not click random page controls.
    """
    try:
        for sel in ("[role='dialog']", "[aria-modal='true']"):
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                if el.is_displayed() and el.find_elements(By.CSS_SELECTOR, "input, select, textarea, button"):
                    return el
        for xp in (
            "//*[contains(@id,'screening') or contains(@id,'Screening') "
            "or contains(@id,'modal') or contains(@id,'Modal')]"
            "[.//input[not(@type='hidden')] or .//select or .//textarea]",
        ):
            for el in driver.find_elements(By.XPATH, xp):
                if not el.is_displayed():
                    continue
                try:
                    h, w = el.size.get("height", 0), el.size.get("width", 0)
                    if h > 2000 and w > 1200:
                        continue
                except Exception:
                    pass
                return el
        for el in driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'modal') or contains(@class,'Modal') or contains(@class,'drawer') "
            "or contains(@class,'Drawer') or contains(@class,'popup') or contains(@class,'Popup') "
            "or contains(@class,'sheet') or contains(@class,'Sheet')]"
            "[not(contains(@class,'srp-job'))]"
            "[.//input[not(@type='hidden')] or .//select or .//textarea or .//button]",
        ):
            if not el.is_displayed():
                continue
            try:
                h, w = el.size.get("height", 0), el.size.get("width", 0)
                if h > 1800 and w > 1100:
                    continue
            except Exception:
                pass
            return el
    except Exception:
        pass
    return None


def _find_fallback_apply_container(driver):
    """
    Naukri sometimes uses a plain form or content block without role=dialog.
    Prefer forms under main/article that look like screening (not site search).
    """
    try:
        for xp in (
            "//main//form[.//textarea or .//select or .//input[@type='radio']]",
            "//article//form[.//textarea or .//select or .//input[@type='radio']]",
            "//form[.//textarea or .//select][not(ancestor::header)][not(ancestor::footer)]",
        ):
            for el in driver.find_elements(By.XPATH, xp):
                if el.is_displayed():
                    if el.find_elements(By.CSS_SELECTOR, "input[type='search']"):
                        continue
                    return el
    except Exception:
        pass
    return None


def _select_best_option(options, answers):
    for option in options:
        option_text = _normalize(option.text)
        for ans in answers:
            if _normalize(ans) in option_text or option_text in _normalize(ans):
                return option
    return None


def _field_key(field):
    parts = [
        field.get_attribute("name"),
        field.get_attribute("id"),
        field.get_attribute("placeholder"),
        field.get_attribute("aria-label"),
        field.get_attribute("data-testid"),
    ]
    try:
        lab = field.find_element(By.XPATH, "./ancestor::label[1]")
        parts.append(lab.text)
    except Exception:
        pass
    return _normalize(" ".join(p for p in parts if p))


def _matches_skip_keywords(text, skip_questions):
    t = _normalize(text)
    return any(k in t for k in skip_questions)


def _click_action_button(driver, root=None):
    ctx = root if root is not None else driver
    rel_xpaths = [
        ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
        ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]",
        ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
        ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
        ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
        ".//*[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
        ".//*[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]",
        ".//*[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
        ".//*[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
        ".//*[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
        ".//input[@type='submit']",
    ]
    for rx in rel_xpaths:
        xp = rx if root is not None else rx.replace(".//", "//", 1)
        for b in ctx.find_elements(By.XPATH, xp):
            if not b.is_displayed() or not b.is_enabled():
                continue
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", b)
            return b.text or b.get_attribute("value") or ""
    return None


def _default_short(config):
    return (config.get("default_short_answer") or "See my Naukri profile for details.").strip()


def _default_paragraph(config):
    s = (config.get("default_paragraph") or "").strip()
    if s:
        return s
    return _default_short(config)


def _fill_one_step(driver, config, root=None):
    ctx = root if root is not None else driver
    skip_questions = [_normalize(q) for q in config.get("skip_questions", [])]

    skip_xp = (
        ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]"
        " | .//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]"
        " | .//*[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]"
    )
    if root is None:
        skip_xp = skip_xp.replace(".//", "//")

    for s in ctx.find_elements(By.XPATH, skip_xp):
        if s.is_displayed():
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", s)
            driver.execute_script("arguments[0].click();", s)
            print("Skipped optional screening step")
            time.sleep(1.5)
            return "skip"

    for radio in ctx.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
        if not radio.is_displayed():
            continue
        val = _normalize(radio.get_attribute("value"))
        try:
            group = radio.find_element(By.XPATH, "ancestor::*[.//text()][1]")
            ctx_txt = _normalize(group.text)
        except Exception:
            ctx_txt = ""
        if _matches_skip_keywords(ctx_txt, skip_questions):
            continue
        if any(k in ctx_txt for k in config.get("yes_no_questions", [])):
            if "yes" in val[:8] or val in ("1", "true", "y"):
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(0.3)
        elif "yes" in val or val in ("1", "true", "y"):
            driver.execute_script("arguments[0].click();", radio)
            time.sleep(0.3)

    for cb in ctx.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        if not cb.is_displayed():
            continue
        label = _normalize(cb.get_attribute("value"))
        try:
            parent_text = _normalize(cb.find_element(By.XPATH, "ancestor::label[1]").text)
        except Exception:
            parent_text = ""
        blob = label + " " + parent_text
        for tech in config.get("technology_answers", []):
            if _normalize(tech) in blob:
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                time.sleep(0.2)

    for sel_el in ctx.find_elements(By.TAG_NAME, "select"):
        if not sel_el.is_displayed():
            continue
        try:
            s_obj = Select(sel_el)
            options = s_obj.options
            if len(options) <= 1:
                continue
            pool = (
                config.get("education_answers", [])
                + config.get("branch_answers", [])
                + config.get("technology_answers", [])
            )
            best = _select_best_option(options, pool)
            if best:
                s_obj.select_by_visible_text(best.text)
            else:
                s_obj.select_by_index(1)
            time.sleep(0.3)
        except Exception:
            continue

    text_map = config.get("text_answers", {})

    for ta in ctx.find_elements(By.TAG_NAME, "textarea"):
        if not ta.is_displayed():
            continue
        key = _field_key(ta)
        if _matches_skip_keywords(key, skip_questions):
            if not (ta.get_attribute("value") or "").strip():
                ta.clear()
                ta.send_keys(_default_paragraph(config)[:1200])
            continue
        answered = False
        for k, v in text_map.items():
            if v is None or (isinstance(v, str) and not str(v).strip()):
                continue
            if _normalize(k) in key:
                ta.clear()
                ta.send_keys(str(v))
                answered = True
                break
        if not answered and not (ta.get_attribute("value") or "").strip():
            ta.clear()
            ta.send_keys(_default_paragraph(config)[:1200])

    for field in ctx.find_elements(By.TAG_NAME, "input"):
        if not field.is_displayed():
            continue
        t = (field.get_attribute("type") or "text").lower()
        if t in ("hidden", "submit", "button", "radio", "checkbox", "file", "search"):
            continue
        key = _field_key(field)
        if _matches_skip_keywords(key, skip_questions):
            continue
        matched = False
        for ans_key, value in text_map.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            if _normalize(ans_key) in key:
                try:
                    field.clear()
                except Exception:
                    pass
                field.send_keys(str(value))
                matched = True
                break
        if matched:
            continue
        if t == "email" or "email" in key or "mail" in key:
            v = text_map.get("email") or text_map.get("e-mail")
            if v:
                try:
                    field.clear()
                except Exception:
                    pass
                field.send_keys(str(v))
            continue
        if t in ("tel", "phone") or "phone" in key or "mobile" in key:
            v = text_map.get("phone") or text_map.get("mobile") or text_map.get("contact")
            if v:
                try:
                    field.clear()
                except Exception:
                    pass
                field.send_keys(str(v))
            continue
        if t in ("text", "number", "tel") and not (field.get_attribute("value") or "").strip():
            try:
                field.clear()
            except Exception:
                pass
            field.send_keys(_default_short(config)[:500])

    clicked = _click_action_button(driver, root=root)
    if clicked:
        low = clicked.lower()
        print(f"Clicked action control: {clicked[:50]}")
        time.sleep(2.5)
        if "submit" in low or ("apply" in low and "company" not in low):
            return "final"
        return "action"

    if root is not None and root.is_displayed():
        return "unchanged"
    if screening_ui_visible(driver):
        return "unchanged"
    return "done"


def _fill_screening_in_current_context(driver, config, root=None):
    time.sleep(1.2)
    for step in range(20):
        try:
            prev = driver.page_source[:5000]
            state = _fill_one_step(driver, config, root=root)
            if state == "final":
                return True
            if state == "done":
                return True
            if state == "unchanged":
                time.sleep(1)
                if driver.page_source[:5000] == prev:
                    break
        except Exception as e:
            print(f"Form step {step}: {e}")
            break
    return True


def fill_form(driver):
    """
    After Apply:
    1) Wait for a screening form/modal UI to appear.
    2) Fill inside that container (or iframe).
    Return True only if we actually detected a screening UI.
    """
    config = load_form_config()
    driver.switch_to.default_content()
    print("Waiting for screening form UI to open...")

    # Try in main document first: root container OR at least visible inputs in a screening flow.
    for _ in range(30):  # ~15s
        root = _find_screening_root(driver)
        if root:
            print("Screening form/modal root found — filling")
            _fill_screening_in_current_context(driver, config, root=root)
            return True

        # Fallback: some Naukri widgets are a plain form/content block without dialog attributes.
        fb = _find_fallback_apply_container(driver)
        if fb:
            print("Screening form (fallback container) found — filling")
            _fill_screening_in_current_context(driver, config, root=fb)
            return True

        # Sometimes we can't identify the root container, but the screening UI is still visible.
        if screening_ui_visible(driver):
            print("Screening UI is visible but root container not identified — filling broadly within UI")
            _fill_screening_in_current_context(driver, config, root=None)
            return True

        time.sleep(0.5)

    # Try iframes (common for embedded application widgets)
    for iframe in driver.find_elements(By.CSS_SELECTOR, "iframe"):
        if not iframe.is_displayed():
            continue
        try:
            driver.switch_to.frame(iframe)
            root = None
            for _ in range(20):  # ~8s
                root = _find_screening_root(driver)
                if root:
                    break
                if screening_ui_visible(driver):
                    print("Screening UI visible inside iframe — filling")
                    _fill_screening_in_current_context(driver, config, root=None)
                    driver.switch_to.default_content()
                    return True
                time.sleep(0.4)

            if not root:
                root = _find_fallback_apply_container(driver)

            if root:
                print("Screening inside iframe (root found) — filling")
                _fill_screening_in_current_context(driver, config, root=root)
                driver.switch_to.default_content()
                return True
        except Exception as e:
            print(f"Iframe screening attempt: {e}")
        finally:
            driver.switch_to.default_content()

    fb = _find_fallback_apply_container(driver)
    if fb:
        print("Screening form (fallback container) — filling")
        _fill_screening_in_current_context(driver, config, root=fb)
        return True

    print("No screening form detected — nothing to fill")
    return False
