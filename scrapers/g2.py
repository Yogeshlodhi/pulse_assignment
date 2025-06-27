# scrapers/g2.py
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

from utils.date_utils import normalize_date, is_within_range


def scrape_g2(company_slug, start_date, end_date):
    options = uc.ChromeOptions()
    
    # to not show the browser window
    # options.add_argument("--headless=new")
    # to not show the browser window
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    # options.headless = True  # Try headless AFTER it works in visible mode

    print("[*] Launching undetected Chrome browser...")
    driver = uc.Chrome(options=options)
    url = f"https://www.g2.com/products/{company_slug}/reviews"
    print(f"[*] Navigating to: {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.paper__bd"))
        )
    except:
        driver.save_screenshot("output/g2_blocked.png")
        print("❌ Reviews not loaded — likely blocked. Screenshot saved.")
        driver.quit()
        return []

    print("[*] Reviews loaded. Parsing...")
    reviews = []
    page = 1

    while True:
        print(f"📄 Scraping page {page}...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        blocks = soup.select("div.paper__bd")
        if not blocks:
            print("[!] No more reviews found.")
            break

        for block in blocks:
            try:
                # print("Block : ", block)
                title_tag = block.select_one('div[itemprop="name"]')
                review_paras = block.select('div[itemprop="reviewBody"] p.formatted-text')
                date_tag = block.select_one('meta[itemprop="datePublished"]')
                rating_div = block.select_one('div.stars')

                title = title_tag.get_text(strip=True) if title_tag else None
                review = "\n".join(p.get_text(strip=True) for p in review_paras)
                date_raw = date_tag.get("content") if date_tag else None
                date = normalize_date(date_raw)
                if not is_within_range(date_raw, start_date, end_date):
                    continue

                rating = None
                if rating_div:
                    for cls in rating_div.get("class", []):
                        if cls.startswith("stars-"):
                            rating = int(cls.split("-")[1]) / 2

                reviews.append({
                    "title": title,
                    "review": review,
                    "date": date,
                    # "reviewer": None,
                    "rating": rating,
                    "source": "G2"
                })
            except Exception as e:
                continue

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, ".pagination__item--next a")
            next_btn.click()
            page += 1
            time.sleep(2)
        except:
            break

    driver.quit()
    print(f"[✓] Scraped {len(reviews)} reviews from G2.")
    return reviews




# import requests
# from bs4 import BeautifulSoup
# from utils.date_utils import is_within_range, normalize_date

# def scrape_g2(company_slug, start_date, end_date):
#     page = 1
#     reviews = []
#     while True:
#         url = f"https://www.g2.com/products/{company_slug}/reviews?page={page}"
#         res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
#         if res.status_code != 200:
#             break

#         print("Response : ", res.text)

#         soup = BeautifulSoup(res.text, "html.parser")
#         review_blocks = soup.select(".paper--no-padding.p-0.mb-3")

#         if not review_blocks:
#             break

#         for block in review_blocks:
#             try:
#                 title = block.select_one("h3").get_text(strip=True)
#                 review = block.select_one(".review-body__content").get_text(strip=True)
#                 date_raw = block.select_one("time").get("datetime")
#                 date = normalize_date(date_raw)
#                 if not is_within_range(date_raw, start_date, end_date):
#                     continue
#                 reviewer = block.select_one(".user-info__name").get_text(strip=True)
#                 rating = int(float(block.select_one("span.star-rating").get("data-rating", "0")))

#                 reviews.append({
#                     "title": title,
#                     "review": review,
#                     "date": date,
#                     "reviewer": reviewer,
#                     "rating": rating,
#                     "source": "G2"
#                 })
#             except Exception as e:
#                 continue
#         page += 1

#     return reviews
