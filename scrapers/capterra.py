# from test import CapterraSeleniumScraper  # adjust import path if needed


# capterra_scraper.py
import json
import time
import random
from datetime import datetime

import dateparser
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class CapterraSeleniumScraper:
    def __init__(self, headless=True):
        options = uc.ChromeOptions()
        options.headless = headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))

    def get_review_url_from_search(self, company_name):
        print(f"🔍 Searching Capterra for '{company_name}'...")
        search_url = f"https://www.capterra.in/search/product?q={company_name}"
        self.driver.get(search_url)
        self.scroll_to_bottom()

        try:
            product_card = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/software/"]')))
            product_href = product_card.get_attribute("href")
            print(f"✅ Found product URL: {product_href}")
            return product_href.replace("/software/", "/reviews/") if "/software/" in product_href else None
        except TimeoutException:
            print("❌ No product found for this company.")
            return None

    def extract_reviews_with_pagination(self, base_url, start_date, end_date):
        self.driver.get(base_url)
        time.sleep(random.uniform(4, 6))

        try:
            most_recent_radio = self.wait.until(
                EC.element_to_be_clickable((By.ID, "opt_most_recent"))
            )
            self.driver.execute_script("arguments[0].click();", most_recent_radio)
            print("✅ Clicked 'Most Recent' filter")
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Could not apply 'Most Recent' filter: {e}")

        all_reviews = []
        page_number = 1

        while True:
            print(f"\n📄 Processing Page {page_number}")
            self.scroll_to_bottom()

            try:
                review_containers = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-entity="review"]'))
                )
            except TimeoutException:
                print("❌ No reviews found or timeout occurred.")
                break

            for container in review_containers:
                review = self._extract_review(container)
                if not review:
                    continue

                parsed_date = dateparser.parse(review.get("review_date", ""))
                if not parsed_date:
                    continue

                if start_date <= parsed_date <= end_date:
                    review["review_date_parsed"] = parsed_date.strftime("%Y-%m-%d")
                    all_reviews.append(review)
                    
                if parsed_date < start_date:
                    print("⏩ Skipping old review (before start_date)")
                    return all_reviews
                    # continue


            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
                if not next_button.is_enabled():
                    break
                print("➡️ Clicking next page...")
                next_button.click()
                time.sleep(random.uniform(8, 12))
                page_number += 1
            except NoSuchElementException:
                print("✅ No more pages.")
                break

        return all_reviews

    def _extract_review(self, container):
        try:
            review = {}

            try:
                review["reviewer_name"] = container.find_element(By.CSS_SELECTOR, ".h5.fw-bold.mb-2").text.strip()
            except NoSuchElementException:
                review["reviewer_name"] = "Anonymous"

            try:
                review["rating"] = container.find_element(By.CSS_SELECTOR, ".star-rating-component .ms-1").text.strip()
            except NoSuchElementException:
                review["rating"] = ""

            try:
                for span in container.find_elements(By.CSS_SELECTOR, ".ms-2"):
                    text = span.text.strip().lower()
                    if any(kw in text for kw in ["ago", "month", "year", "last"]):
                        review["review_date"] = span.text.strip()
                        break
            except NoSuchElementException:
                review["review_date"] = ""

            try:
                review["review_title"] = container.find_element(By.CSS_SELECTOR, "h3.h5.fw-bold").text.strip()
            except NoSuchElementException:
                review["review_title"] = ""

            try:
                for p in container.find_elements(By.TAG_NAME, "p"):
                    if "Comments:" in p.text:
                        review["main_comment"] = p.text.split("Comments:", 1)[1].strip()
                        break
            except NoSuchElementException:
                review["main_comment"] = ""

            return review

        except Exception as e:
            print(f"❌ Error parsing review: {e}")
            return None

    def close(self):
        self.driver.quit()

    def scrape(self, company_name: str, start: datetime, end: datetime):
        try:
            review_url = self.get_review_url_from_search(company_name)
            if not review_url:
                print(f"❌ Could not find review page for: {company_name}")
                return []

            print(f"\n🚀 Scraping reviews from: {review_url}")
            print(f"📅 Date range: {start.date()} to {end.date()}")
            # print(f"📅 Date range: {start} to {end}")
            reviews = self.extract_reviews_with_pagination(review_url, start, end)
            return reviews

        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return []
        finally:
            self.close()



def scrape_capterra(company, start_date, end_date):
    scraper = CapterraSeleniumScraper(headless=True)  # or False for debugging
    return scraper.scrape(company_name=company, start=start_date, end=end_date)
