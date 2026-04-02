# import time
# import json
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# from database import Database
# from job_filter import valid_experience, valid_technology
# from form_filler import fill_form

# import os
# from dotenv import load_dotenv

# load_dotenv()


# class JobBot:

#     def __init__(self):

#         with open("config.json") as f:
#             self.config = json.load(f)

#         self.roles = self.config["roles"]
#         self.technologies = self.config["technologies"]
#         self.max_apply = self.config["max_apply"]

#         chrome_options = Options()
#         chrome_options.add_argument("--start-maximized")

#         self.driver = webdriver.Chrome(options=chrome_options)
#         self.wait = WebDriverWait(self.driver, 15)

#         self.db = Database(self.config)

#     def login(self):

#         print("Logging in...")

#         self.driver.get("https://www.naukri.com/nlogin/login")

#         time.sleep(4)


#         email = os.getenv("NAUKRI_EMAIL")
#         password = os.getenv("NAUKRI_PASSWORD")

#         self.driver.find_element(By.ID, "usernameField").send_keys(email)
#         self.driver.find_element(By.ID, "passwordField").send_keys(password)

#         self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

#         time.sleep(6)

#         print("Login success")

#     def search_jobs(self, role):

#         print("Searching:", role)

#         url = f"https://www.naukri.com/{role.replace(' ','-')}-jobs"

#         self.driver.get(url)

#         self.wait.until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper"))
#         )

#         for _ in range(3):
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
#             time.sleep(3)

#     def get_jobs(self):

#         jobs = self.driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")

#         print("Jobs found:", len(jobs))

#         return jobs

#     def valid_date(self, text):

#         text = text.lower()

#         allowed = [
#             "just now",
#             "today",
#             "1 day",
#             "2 days",
#             "3 days",
#             "4 days",
#             "5 days",
#             "6 days",
#             "7 days",
#             "1 week",
#             "2 weeks"
#         ]

#         for a in allowed:
#             if a in text:
#                 return True

#         return False

#     def remove_overlays(self):

#         try:
#             self.driver.execute_script("""
#                 let overlays = document.querySelectorAll(
#                     '.chatbot_Overlay, .ReactModal__Overlay, .styles_privacyPolicy__yEgp3'
#                 );
#                 overlays.forEach(el => el.remove());
#             """)
#             print("Overlay removed")

#         except:
#             pass

#     def run(self):

#         self.login()

#         applied = 0

#         for role in self.roles:

#             self.search_jobs(role)

#             jobs = self.get_jobs()

#             for job in jobs:

#                 if applied >= self.max_apply:
#                     print("Daily limit reached")
#                     return

#                 try:

#                     title = job.find_element(By.CSS_SELECTOR, "a.title").text
#                     company = job.find_element(By.CSS_SELECTOR, "a.comp-name").text
#                     date = job.find_element(By.CSS_SELECTOR, "span.job-post-day").text

#                     print("Opening job:", title)

#                     if not self.valid_date(date):
#                         continue

#                     if self.db.job_exists(title, company):
#                         continue

#                     link = job.find_element(By.CSS_SELECTOR, "a.title").get_attribute("href")

#                     self.driver.execute_script("window.open(arguments[0])", link)
#                     self.driver.switch_to.window(self.driver.window_handles[1])

#                     time.sleep(4)

#                     try:
#                         description = self.driver.find_element(By.TAG_NAME, "body").text.lower()
#                     except:
#                         description = self.driver.page_source.lower()

#                     if not valid_experience(description):
#                         print("Experience not suitable")
#                         self.driver.close()
#                         self.driver.switch_to.window(self.driver.window_handles[0])
#                         continue

#                     print("Checking technologies:", self.technologies)

#                     if not valid_technology(description, self.technologies):
#                         print("Technology mismatch")
#                         self.driver.close()
#                         self.driver.switch_to.window(self.driver.window_handles[0])
#                         continue

#                     try:

#                         print("Searching for Apply or Share Interest...")

#                         self.remove_overlays()

#                         apply_btn = WebDriverWait(self.driver, 10).until(
#                             EC.presence_of_element_located(
#                                 (
#                                     By.XPATH,
#                                     "//button[contains(.,'Apply') or contains(.,'Share Interest') or contains(.,'I am Interested')]"
#                                     " | //a[contains(.,'Apply') or contains(.,'Share Interest') or contains(.,'I am Interested')]"
#                                     " | //span[contains(.,'Apply') or contains(.,'Share Interest') or contains(.,'I am Interested')]"
                                    
#                                 )
#                             )
#                         )

#                         btn_text = apply_btn.text.lower()

#                         if "company site" in btn_text or "applied" in btn_text:
#                             print("External company apply detected. Skipping.")
#                             self.driver.close()
#                             self.driver.switch_to.window(self.driver.window_handles[0])
#                             continue

#                         self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_btn)
#                         time.sleep(2)

#                         self.remove_overlays()

#                         self.driver.execute_script("arguments[0].click();", apply_btn)

#                         print("Apply button clicked")

#                         time.sleep(4)

#                     except Exception as e:

#                         print("Apply button not found:", e)

#                         self.driver.close()
#                         self.driver.switch_to.window(self.driver.window_handles[0])
#                         continue

#                     time.sleep(2)

#                     page_text = self.driver.page_source.lower()

#                     if any(x in page_text for x in [
#                         "application submitted",
#                         "successfully applied",
#                         "thank you for applying",
#                         "application received",
#                         "applied",
#                         "applied successfully"
#                     ]):
#                         self.db.save_job(title, company, "Naukri")

#                         applied += 1

#                         print("Applied:", title)

#                         self.driver.close()
#                         self.driver.switch_to.window(self.driver.window_handles[0])
#                         continue

#                     success = fill_form(self.driver)

#                     if success:

#                         page_text = self.driver.page_source.lower()

#                         success_keywords=[
#                             "application submitted",
#                             "successfully applied",
#                             "thank you for applying",
#                             "application received",
#                             "applied",
#                             "applied successfully"
#                         ]

#                         if any(k in page_text for k in success_keywords):

#                             self.db.save_job(title, company, "Naukri")

#                             applied += 1

#                             print("Applied:", title)

#                     else:

#                         print("Form filling failed")

#                     self.driver.close()

#                     self.driver.switch_to.window(self.driver.window_handles[0])

#                 except Exception as e:

#                     print("Skipped:", e)

#                     if len(self.driver.window_handles) > 1:
#                         self.driver.close()
#                         self.driver.switch_to.window(self.driver.window_handles[0])

#         print("Run completed")

import time
import json
import re
import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from database import Database
from job_filter import should_skip_job_by_title, valid_experience, valid_technology
from form_filler import fill_form
from job_content import (
    collect_location_corpus,
    extract_locations,
    text_for_experience_check,
    text_for_technology_matching,
)

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

    def remove_overlays(self):
        try:
            self.driver.execute_script(
                """
                document.querySelectorAll(
                  '.chatbot_Overlay, .ReactModal__Overlay, [class*="privacyPolicy"], [id*="chatbot"]'
                ).forEach(function (el) { try { el.remove(); } catch (e) {} });
                """
            )
        except Exception:
            pass

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

    def _naukri_apply_success_in_text(self, body_text: str) -> bool:
        markers = (
            "application submitted",
            "successfully applied",
            "thank you for applying",
            "you have applied",
            "you have successfully applied",
            "already applied to this job",
            "already applied for this job",
            "application has been submitted",
            "your application has been submitted",
            "we have received your application",
        )
        bt = (body_text or "").lower()
        return any(m in bt for m in markers)

    def _naukri_apply_success_visible(self):
        try:
            body = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            body = ""
        return self._naukri_apply_success_in_text(body)

    def _click_naukri_save_job_bookmark(self):
        """Bookmark job on Naukri (same control as external-flow Save)."""
        try:
            save_btn = WebDriverWait(self.driver, 6).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[.//text()[contains(.,'Save')]] | "
                        "//button[contains(.,'Save') or contains(@class,'styles_save-job-button__WLm_s')]",
                    )
                )
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save_btn)
            time.sleep(0.3)
            self.remove_overlays()
            self.driver.execute_script("arguments[0].click();", save_btn)
            print("Saved job on Naukri (bookmark fallback)")
            return True
        except Exception as e:
            print("Could not click Save job:", e)
            return False

    def get_jobs(self):

        jobs = self.driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")

        print("Jobs found:", len(jobs))

        return jobs
    
    def valid_date(self, text):

        text = text.lower().strip()

        # today or just now
        if "today" in text or "just now" in text:
            return True

        import re

        match = re.search(r"(\d+)\s*(day|days|week|weeks)", text)

        if match:
            value = int(match.group(1))
            unit = match.group(2)

            if "day" in unit:
                return value <= 7

            if "week" in unit:
                return value <= 2

        return False

    def search_jobs(self, role, location, page=1):
        role_slug = role.strip().lower().replace(" ", "-")
        loc_slug = location.strip().lower().replace(" ", "-")
        print(f"Searching: {role} | Location: {location} | Page: {page}")

        if page == 1:
            url = f"https://www.naukri.com/{role_slug}-jobs-in-{loc_slug}"
        else:
            url = f"https://www.naukri.com/{role_slug}-jobs-in-{loc_slug}-{page}"

        self.driver.get(url)

        try:
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper"))
            )
        except TimeoutException:
            print(f"No listing UI (timeout or zero results): {url}")
            return False

        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

        return True

    def run(self):
        self.login()
        applied = 0
        locs = self.config["locations"]

        for role in self.roles:
            for location in locs:
                if applied >= self.max_apply:
                    print("Daily limit reached")
                    return

                for page_num in range(1, 4):
                    if applied >= self.max_apply:
                        print("Daily limit reached")
                        return

                    if not self.search_jobs(role, location, page=page_num):
                        break

                    jobs = self.get_jobs()

                    if not jobs:
                        break

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

                            if should_skip_job_by_title(title):
                                print("Title looks non-tech — skip without opening")
                                continue

                            link = job.find_element(By.CSS_SELECTOR, "a.title").get_attribute("href")

                            self.driver.execute_script("window.open(arguments[0])", link)
                            self.driver.switch_to.window(self.driver.window_handles[1])

                            time.sleep(1)

                            jd_for_tech = text_for_technology_matching(self.driver)
                            if len(jd_for_tech.strip()) < 120:
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                                time.sleep(1)
                                jd_for_tech = text_for_technology_matching(self.driver)

                            if not jd_for_tech.strip():
                                print("No JD text — skip (skills check)")
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                continue

                            jd_for_exp = text_for_experience_check(self.driver)

                            if not valid_experience(jd_for_exp):
                                print("Experience not suitable")
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                continue

                            if not valid_technology(jd_for_tech, self.technologies, quiet=True):
                                print("Technology mismatch — skip")
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                continue

                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1.5)
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1.5)

                            loc_corpus = collect_location_corpus(self.driver)

                            _ap = (
                                "concat(' ', translate(normalize-space(.), "
                                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), ' ')"
                            )
                            apply_only_xpath = (
                                f"//button[contains({_ap}, ' apply ') and not(contains({_ap}, ' applied '))]"
                                f" | //a[contains({_ap}, ' apply ') and not(contains({_ap}, ' applied '))]"
                                f" | //span[contains({_ap}, ' apply ') and not(contains({_ap}, ' applied '))]"
                            )
                            apply_interest_xpath = (
                                f"//button[contains({_ap}, ' share interest ')]"
                                f" | //a[contains({_ap}, ' share interest ')]"
                                f" | //button[contains({_ap}, ' i am interested ')]"
                                f" | //a[contains({_ap}, ' i am interested ')]"
                            )

                            try:
                                print("Searching for Apply or Share Interest...")
                                self.remove_overlays()
                                try:
                                    apply_btn = WebDriverWait(self.driver, 12).until(
                                        EC.element_to_be_clickable((By.XPATH, apply_only_xpath))
                                    )
                                except TimeoutException:
                                    apply_btn = WebDriverWait(self.driver, 8).until(
                                        EC.element_to_be_clickable(
                                            (By.XPATH, apply_interest_xpath)
                                        )
                                    )

                                btn_text = (apply_btn.text or "").lower()

                                if "already applied" in btn_text:
                                    print("Already applied on Naukri — closing")
                                    self.driver.close()
                                    self.driver.switch_to.window(self.driver.window_handles[0])
                                    continue

                                if (
                                    "company site" in btn_text
                                    or "company website" in btn_text
                                    or "employer site" in btn_text
                                ):
                                    print(
                                        "Apply on company site — Save on Naukri profile only (not stored in local DB)"
                                    )

                                    try:
                                        save_btn = WebDriverWait(self.driver, 5).until(
                                            EC.element_to_be_clickable(
                                                (
                                                    By.XPATH,
                                                    "//button[.//text()[contains(.,'Save')]] | //button[contains(.,'Save') or contains(@class,'styles_save-job-button__WLm_s')]",
                                                )
                                            )
                                        )
                                        self.driver.execute_script("arguments[0].click();", save_btn)
                                        print("Saved on Naukri (company-site flow), local DB unchanged")
                                    except Exception as e:
                                        print("Save button not found:", e)

                                    self.driver.close()
                                    self.driver.switch_to.window(self.driver.window_handles[0])
                                    continue

                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block:'center'});", apply_btn
                                )
                                time.sleep(0.5)
                                self.remove_overlays()
                                # Avoid false positives: the page may already contain "already applied"
                                # messages before clicking Apply. We only treat it as a new success if
                                # success appears after the click.
                                pre_success = self._naukri_apply_success_visible()
                                print("Pre-apply success text detected:", pre_success)
                                self.driver.execute_script("arguments[0].click();", apply_btn)
                                print("Apply clicked → direct success, else screening form, else bookmark")

                                time.sleep(5)
                                self.remove_overlays()

                                if self._naukri_apply_success_visible() and not pre_success:
                                    job_locations = extract_locations(
                                        loc_corpus, self.config["locations"]
                                    )
                                    self.db.save_job(title, company, "Naukri", job_locations)
                                    applied += 1
                                    print("Applied (direct):", title)
                                else:
                                    print("Direct success not detected → attempting to fill screening form")
                                    form_found = fill_form(self.driver)
                                    time.sleep(2)
                                    self.remove_overlays()
                                    if self._naukri_apply_success_visible():
                                        job_locations = extract_locations(
                                            loc_corpus, self.config["locations"]
                                        )
                                        self.db.save_job(title, company, "Naukri", job_locations)
                                        applied += 1
                                        print("Applied (after screening form):", title)
                                    else:
                                        if not form_found:
                                            print("Form not detected — saving on Naukri only")
                                            if self._click_naukri_save_job_bookmark():
                                                print(
                                                    "Saved job on Naukri profile only (form not detected; not in local DB):",
                                                    title,
                                                )
                                            else:
                                                print("Could not save on Naukri — Skipping")
                                        else:
                                            print("Retry screening form (late load)")
                                            fill_form(self.driver)
                                            time.sleep(2)
                                            self.remove_overlays()
                                            if self._naukri_apply_success_visible():
                                                job_locations = extract_locations(
                                                    loc_corpus, self.config["locations"]
                                                )
                                                self.db.save_job(title, company, "Naukri", job_locations)
                                                applied += 1
                                                print("Applied (after 2nd form pass):", title)
                                            elif self._click_naukri_save_job_bookmark():
                                                print(
                                                    "Saved job on Naukri profile only (apply not confirmed; not in local DB):",
                                                    title,
                                                )
                                            else:
                                                print("Could not apply, form, or bookmark — Skipping")

                            except Exception as e:
                                print("Apply button not found:", e)
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                continue

                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])

                        except Exception as e:
                            print("Skipped:", e)
                            if len(self.driver.window_handles) > 1:
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])

        print("Run completed")




