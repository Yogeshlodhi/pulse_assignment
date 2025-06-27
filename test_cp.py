import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser
import json
import time
import re
import random
from urllib.parse import quote
import sys
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (WebDriverException, 
                                     TimeoutException,
                                     NoSuchElementException)

class CapterraScraper:
    def __init__(self, company_name, start_date, end_date, output_file, use_selenium=False):
        self.company_name = company_name
        self.start_date = parser.parse(start_date).date() if start_date else None
        self.end_date = parser.parse(end_date).date() if end_date else None
        self.output_file = output_file
        self.base_url = "https://www.capterra.com"
        self.reviews = []
        self.ua = UserAgent()
        self.use_selenium = use_selenium
        self.driver = None
        self.max_retries = 3
        
        if self.use_selenium:
            self.init_selenium()

    def init_selenium(self, headless=True):
        """Initialize Selenium WebDriver with retries"""
        for attempt in range(self.max_retries):
            try:
                options = Options()
                if headless:
                    options.add_argument("--headless=new")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument(f"user-agent={self.ua.random}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.set_page_load_timeout(30)
                return True
                
            except WebDriverException as e:
                print(f"Attempt {attempt + 1} failed: {str(e).split('\n')[0]}")
                if attempt == self.max_retries - 1:
                    print("\nSelenium initialization failed. Possible solutions:")
                    print("1. Make sure Chrome is installed (https://www.google.com/chrome/)")
                    print("2. Update Chrome: 'sudo apt-get --only-upgrade install google-chrome-stable'")
                    print("3. Try running without headless mode")
                    print("4. Run with 'sudo' if on Linux")
                    return False
                time.sleep(5)

    def search_company_selenium(self):
        """Search using Selenium with enhanced waiting"""
        if not self.driver:
            if not self.init_selenium(headless=False):  # Try without headless first
                return None
                
        search_url = f"{self.base_url}/search/?query={quote(self.company_name)}"
        
        try:
            print(f"Loading search page: {search_url}")
            self.driver.get(search_url)
            
            # Wait for either search results or CAPTCHA
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, ".ProductCardWrapper") or 
                    "captcha" in d.page_source.lower() or
                    d.find_elements(By.ID, "challenge-running")
                )
            except TimeoutException:
                print("Timed out waiting for search results")
                self.debug_page("search_timeout")
                return None
                
            # Check for Cloudflare or CAPTCHA
            if any(text in self.driver.page_source.lower() 
                  for text in ["captcha", "challenge", "cloudflare"]):
                print("Security challenge detected. Possible solutions:")
                print("1. Try again later")
                print("2. Use a different network/VPN")
                print("3. Manually solve CAPTCHA in visible browser")
                self.debug_page("captcha_detected")
                return None
                
            # Check for search results
            try:
                product_cards = self.driver.find_elements(By.CSS_SELECTOR, ".ProductCardWrapper")
                if not product_cards:
                    print("No search results found")
                    return None
                    
                # Try to find exact match
                for card in product_cards:
                    try:
                        name = card.find_element(By.CSS_SELECTOR, ".ProductCard__Name").text
                        if self.company_name.lower() in name.lower():
                            link = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                            return f"{link}/reviews/"
                    except NoSuchElementException:
                        continue
                
                # Fallback to first result
                first_link = product_cards[0].find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                print(f"Using first result: {first_link}")
                return f"{first_link}/reviews/"
                
            except NoSuchElementException as e:
                print(f"Element not found: {e}")
                return None
                
        except Exception as e:
            print(f"Search error: {e}")
            return None

    def debug_page(self, prefix=""):
        """Save debug information"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}"
            
            # Save screenshot
            self.driver.save_screenshot(f"{filename}.png")
            print(f"Screenshot saved as {filename}.png")
            
            # Save page source
            with open(f"{filename}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Page source saved as {filename}.html")
            
        except Exception as e:
            print(f"Could not save debug info: {e}")

    def run(self):
        """Main execution method with fallback logic"""
        print(f"\nStarting Capterra scraper for {self.company_name}")
        print(f"Date range: {self.start_date} to {self.end_date}")
        
        # First try with Selenium
        product_url = self.search_company_selenium()
        
        if not product_url and not self.use_selenium:
            print("\nFalling back to requests method...")
            self.use_selenium = False
            product_url = self.search_company_requests()
        
        if not product_url:
            print("\nFailed to find product page after all attempts")
            return False
            
        print(f"\nFound product page: {product_url}")
        print("Starting review scraping...")
        
        self.scrape_reviews(product_url)
        
        if self.reviews:
            print(f"\nSuccess! Found {len(self.reviews)} reviews")
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.reviews, f, indent=2, ensure_ascii=False)
                print(f"Results saved to {self.output_file}")
                return True
            except Exception as e:
                print(f"Error saving results: {e}")
                return False
        else:
            print("\nNo reviews found matching criteria")
            return False

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

def main():
    if len(sys.argv) < 5:
        print("Usage: python capterra_scraper.py <company_name> <start_date> <end_date> <output_file> [--selenium]")
        print("Example: python capterra_scraper.py Zoom 2023-01-01 2023-12-31 zoom_reviews.json --selenium")
        sys.exit(1)
        
    company_name = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    output_file = sys.argv[4]
    use_selenium = '--selenium' in sys.argv
    
    # Validate dates
    try:
        start_dt = parser.parse(start_date)
        end_dt = parser.parse(end_date)
        if start_dt > end_dt:
            print("Error: Start date must be before end date")
            sys.exit(1)
        if end_dt > datetime.now():
            print("Warning: End date is in the future")
    except ValueError as e:
        print(f"Invalid date format: {e}")
        sys.exit(1)
    
    print("\nTROUBLESHOOTING TIPS:")
    print("1. If you get timeouts or CAPTCHAs:")
    print("   - Try running without --selenium flag first")
    print("   - Use a VPN to change your IP address")
    print("   - Wait a few minutes between attempts")
    print("2. For Selenium errors:")
    print("   - Ensure Chrome is installed and updated")
    print("   - Run with 'sudo' if on Linux")
    print("   - Try visible browser mode (edit script)\n")
    
    scraper = CapterraScraper(company_name, start_date, end_date, output_file, use_selenium)
    success = scraper.run()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()