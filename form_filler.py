import json
import time
from selenium.webdriver.common.by import By


def load_form_config():

    with open("form_answer.json") as f:
        return json.load(f)


def keyword_match(text, keywords):

    text = text.lower()

    for k in keywords:
        if k in text:
            return True

    return False


def select_best_option(options, answers):

    for option in options:

        option_text = option.text.lower()

        for ans in answers:

            if ans.lower() in option_text:
                return option

    return None


def fill_form(driver):

    config = load_form_config()

    try:

        # -------- TEXT INPUTS --------

        inputs = driver.find_elements(By.TAG_NAME, "input")

        for field in inputs:

            try:

                name = (
                    field.get_attribute("name")
                    or field.get_attribute("placeholder")
                    or ""
                ).lower()

                for key, value in config["text_answers"].items():

                    if key in name:

                        field.clear()
                        field.send_keys(value)

            except:
                pass


        # -------- TEXTAREA --------

        textareas = driver.find_elements(By.TAG_NAME, "textarea")

        for ta in textareas:

            question = (
                ta.get_attribute("name")
                or ta.get_attribute("placeholder")
                or ""
            ).lower()

            if keyword_match(question, config["skip_questions"]):
                return False


        # -------- DROPDOWNS --------

        selects = driver.find_elements(By.TAG_NAME, "select")

        for select in selects:

            options = select.find_elements(By.TAG_NAME, "option")

            best = select_best_option(
                options,
                config["education_answers"]
                + config["branch_answers"]
                + config["technology_answers"]
            )

            if best:
                best.click()
            elif len(options) > 1:
                options[1].click()


        # -------- YES/NO --------

        radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")

        for radio in radios:

            value = (radio.get_attribute("value") or "").lower()

            if "yes" in value:
                radio.click()


        # -------- CHECKBOX --------

        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

        for cb in checkboxes:

            label = (cb.get_attribute("value") or "").lower()

            for tech in config["technology_answers"]:

                if tech.lower() in label:
                    cb.click()


        time.sleep(2)

        # -------- SUBMIT --------

        buttons = driver.find_elements(By.TAG_NAME, "button")

        for b in buttons:

            txt = b.text.lower()

            if "submit" in txt or "apply" in txt or "next" in txt:

                b.click()
                time.sleep(2)
                return True

        return True

    except:

        return False