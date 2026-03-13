import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from database import Database
from job_filter import valid_experience, valid_technology
from form_filler import fill_form

import os
from dotenv import load_dotenv

load_dotenv()


class JobBot:

    def __init__(self):

        with open("config.json") as f:
            self.config = json.load(f)

        self.roles = self.config["roles"]
        self.technologies = self.config["technologies"]
        self.max_apply = self.config["max_apply"]

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

        self.db = Database(self.config)

    def login(self):

        print("Logging in...")

        self.driver.get("https://www.naukri.com/nlogin/login")

        time.sleep(4)


        email = os.getenv("NAUKRI_EMAIL")
        password = os.getenv("NAUKRI_PASSWORD")

        self.driver.find_element(By.ID, "usernameField").send_keys(email)
        self.driver.find_element(By.ID, "passwordField").send_keys(password)

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

        time.sleep(6)

        print("Login success")

    def search_jobs(self, role):

        print("Searching:", role)

        url = f"https://www.naukri.com/{role.replace(' ','-')}-jobs"

        self.driver.get(url)

        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper"))
        )

        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

    def get_jobs(self):

        jobs = self.driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")

        print("Jobs found:", len(jobs))

        return jobs

    def valid_date(self, text):

        text = text.lower()

        allowed = [
            "today",
            "1 day",
            "2 days",
            "3 days",
            "4 days",
            "5 days",
            "6 days",
            "7 days",
            "1 week",
            "2 weeks"
        ]

        for a in allowed:
            if a in text:
                return True

        return False

    def run(self):

        self.login()

        applied = 0

        for role in self.roles:

            self.search_jobs(role)

            jobs = self.get_jobs()

            for job in jobs:

                if applied >= self.max_apply:
                    print("Daily limit reached")
                    return

                try:

                    title = job.find_element(By.CSS_SELECTOR, "a.title").text
                    company = job.find_element(By.CSS_SELECTOR, "a.comp-name").text
                    date = job.find_element(By.CSS_SELECTOR, "span.job-post-day").text

                    print("Opening job:", title)

                    if not self.valid_date(date):
                        continue

                    if self.db.job_exists(title, company):
                        continue

                    link = job.find_element(By.CSS_SELECTOR, "a.title").get_attribute("href")

                    self.driver.execute_script("window.open(arguments[0])", link)
                    self.driver.switch_to.window(self.driver.window_handles[1])

                    time.sleep(4)

                    try:
                        description = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    except:
                        description = self.driver.page_source.lower()

                    if not valid_experience(description):
                        print("Experience not suitable")
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        continue

                    print("Checking technologies:", self.technologies)

                    if not valid_technology(description, self.technologies):
                        print("Technology mismatch")
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        continue

                    try:

                        print("Searching for Apply or Share Interest...")

                        apply_btn = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH,
                                    "//button[contains(.,'Apply') or contains(.,'Share Interest')]"
                                    " | //a[contains(.,'Apply') or contains(.,'Share Interest')]"
                                    " | //span[contains(.,'Apply') or contains(.,'Share Interest')]"
                                )
                            )
                        )

                        btn_text = apply_btn.text.lower()

                        if "company site" in btn_text or "applied" in btn_text:
                            print("External company apply detected. Skipping.")
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                            continue

                        self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_btn)
                        time.sleep(2)

                        self.driver.execute_script("arguments[0].click();", apply_btn)

                        print("Apply button clicked")

                        time.sleep(4)

                    except Exception as e:

                        print("Apply button not found:", e)

                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        continue

                    success = fill_form(self.driver)

                    if success:

                        self.db.save_job(title, company, "Naukri")

                        applied += 1

                        print("Applied:", title)

                    else:

                        print("Form filling failed")

                    self.driver.close()

                    self.driver.switch_to.window(self.driver.window_handles[0])

                except Exception as e:

                    print("Skipped:", e)

                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

        print("Run completed")