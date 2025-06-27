#!/usr/bin/env python3
"""
Advanced Capterra Reviews Scraper
Built to handle anti-bot protection and extract reviews efficiently
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote, urlparse
from bs4 import BeautifulSoup
import argparse
import logging
from typing import List, Dict, Optional
import re
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('capterra_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CapterraReviewsScraper:
    def __init__(self, use_selenium=False):
        self.base_url = "https://www.capterra.com"
        self.use_selenium = use_selenium
        
        if use_selenium:
            self.setup_selenium()
        else:
            self.setup_cloudscraper()
    
    def setup_cloudscraper(self):
        """Setup CloudScraper to bypass Cloudflare protection"""
        try:
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                },
                delay=10,
                debug=False
            )
            logger.info("CloudScraper initialized successfully")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def save_to_csv(self, reviews: List[Dict], filename: str):
        """Save reviews to CSV format for easy viewing"""
        try:
            import csv
            
            if not reviews:
                return
            
            # Get all possible fields
            all_fields = set()
            for review in reviews:
                all_fields.update(review.keys())
            
            fieldnames = ['title', 'description', 'date', 'rating', 'reviewer_name', 'reviewer_company'] + \
                        list(all_fields - {'title', 'description', 'date', 'rating', 'reviewer_name', 'reviewer_company'})
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for review in reviews:
                    # Clean up description for CSV
                    if 'description' in review:
                        review['description'] = review['description'].replace('\n', ' ').replace('\r', ' ')
                    writer.writerow(review)
            
            logger.info(f"CSV saved to {filename}")
            
        except Exception as e:
            logger.warning(f"Could not save CSV: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.use_selenium and hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("Selenium driver closed")
            except Exception as e:
                logger.warning(f"Error closing Selenium driver: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Advanced Capterra Reviews Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python capterra_scraper.py --company "Salesforce" --start-date "2023-01-01" --end-date "2023-12-31"
  python capterra_scraper.py --company "HubSpot" --start-date "2023-06-01" --end-date "2023-12-31" --selenium
  python capterra_scraper.py --company "Slack" --start-date "2023-01-01" --end-date "2023-12-31" --output "slack_reviews.json" --verbose
        """
    )
    
    parser.add_argument('--company', required=True, 
                       help='Company name to search for')
    parser.add_argument('--start-date', required=True, 
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, 
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='capterra_reviews.json', 
                       help='Output JSON file name (default: capterra_reviews.json)')
    parser.add_argument('--selenium', action='store_true', 
                       help='Use Selenium WebDriver (slower but more reliable)')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--delay-min', type=float, default=2.0,
                       help='Minimum delay between requests in seconds (default: 2.0)')
    parser.add_argument('--delay-max', type=float, default=7.0,
                       help='Maximum delay between requests in seconds (default: 7.0)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate dates
    try:
        start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        if start_dt > end_dt:
            print("Error: Start date must be before end date")
            return
        
        if end_dt > datetime.now():
            print("Warning: End date is in the future")
    
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD")
        return
    
    print(f"🚀 Starting Capterra scraper for '{args.company}'")
    print(f"📅 Date range: {args.start_date} to {args.end_date}")
    print(f"🔧 Mode: {'Selenium WebDriver' if args.selenium else 'CloudScraper'}")
    print(f"⏱️  Delay range: {args.delay_min}-{args.delay_max} seconds")
    print(f"📁 Output: {args.output}")
    print("-" * 50)
    
    scraper = CapterraReviewsScraper(use_selenium=args.selenium)
    
    try:
        # Override delay settings if provided
        scraper.random_delay = lambda: time.sleep(random.uniform(args.delay_min, args.delay_max))
        
        reviews = scraper.scrape_reviews(args.company, args.start_date, args.end_date)
        
        if reviews:
            scraper.save_to_json(reviews, args.output, args.company, args.start_date, args.end_date)
            
            print(f"\n✅ Success! Scraped {len(reviews)} reviews")
            print(f"📄 Saved to: {args.output}")
            print(f"📊 CSV also saved to: {args.output.replace('.json', '.csv')}")
            
            # Quick stats
            rated_reviews = [r for r in reviews if r.get('rating')]
            if rated_reviews:
                avg_rating = sum(r['rating'] for r in rated_reviews) / len(rated_reviews)
                print(f"⭐ Average rating: {avg_rating:.1f}/5.0 ({len(rated_reviews)} rated reviews)")
            
            dated_reviews = [r for r in reviews if r.get('date')]
            print(f"📅 Reviews with dates: {len(dated_reviews)}/{len(reviews)}")
            
        else:
            print("\n❌ No reviews found. Possible reasons:")
            print("   • Company name not found on Capterra")
            print("   • No reviews in the specified date range")
            print("   • Anti-bot protection blocked the scraper")
            print("   • Try using --selenium flag for better success rate")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Error occurred: {e}")
        print("💡 Try running with --verbose flag for more details")
        print("💡 Consider using --selenium flag if getting 403 errors")
        
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main() Exception as e:
        logger.error(f"Failed to initialize CloudScraper: {e}")
        self.setup_requests_session()
    
    def setup_requests_session(self):
        """Fallback to requests with enhanced headers"""
        self.scraper = requests.Session()
        
        # Enhanced headers to mimic real browser
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.current_ua = random.choice(user_agents)
        
        headers = {
            'User-Agent': self.current_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"'
        }
        
        self.scraper.headers.update(headers)
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504, 403]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.scraper.mount("http://", adapter)
        self.scraper.mount("https://", adapter)
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for JavaScript-heavy pages"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            
            # Randomize window size
            window_sizes = [(1366, 768), (1920, 1080), (1440, 900), (1536, 864)]
            width, height = random.choice(window_sizes)
            chrome_options.add_argument(f"--window-size={width},{height}")
            
            # Install and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
            self.setup_cloudscraper()
    
    def random_delay(self, min_delay=2, max_delay=7):
        """Smart delay with human-like patterns"""
        delay = random.uniform(min_delay, max_delay)
        
        # Add occasional longer pauses (10% chance)
        if random.random() < 0.1:
            delay += random.uniform(5, 15)
        
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def get_page_content(self, url: str, retries=3) -> Optional[BeautifulSoup]:
        """Get page content with multiple fallback methods"""
        for attempt in range(retries):
            try:
                if self.use_selenium:
                    return self.get_page_selenium(url)
                else:
                    return self.get_page_requests(url)
            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    self.random_delay(5, 15)  # Longer delay on retry
                    # Switch method on retry
                    if not self.use_selenium and attempt == 1:
                        logger.info("Switching to Selenium for retry")
                        self.setup_selenium()
                        if not hasattr(self, 'driver'):
                            continue
        
        logger.error(f"Failed to get content from {url} after {retries} attempts")
        return None
    
    def get_page_requests(self, url: str) -> BeautifulSoup:
        """Get page using requests/cloudscraper"""
        self.random_delay()
        response = self.scraper.get(url, timeout=30)
        response.raise_for_status()
        
        if response.status_code == 403:
            raise requests.exceptions.HTTPError("403 Forbidden - Consider using Selenium mode")
        
        return BeautifulSoup(response.content, 'html.parser')
    
    def get_page_selenium(self, url: str) -> BeautifulSoup:
        """Get page using Selenium WebDriver"""
        self.driver.get(url)
        
        # Wait for page to load
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Scroll to simulate human behavior
        self.human_scroll()
        
        # Random additional wait
        time.sleep(random.uniform(2, 5))
        
        return BeautifulSoup(self.driver.page_source, 'html.parser')
    
    def human_scroll(self):
        """Simulate human scrolling behavior"""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            
            while current_position < total_height:
                # Random scroll distance
                scroll_distance = random.randint(300, 800)
                current_position += scroll_distance
                
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.5, 2))
                
                # Update total height (in case of dynamic loading)
                total_height = self.driver.execute_script("return document.body.scrollHeight")
        
        except Exception as e:
            logger.debug(f"Scrolling simulation failed: {e}")
    
    def search_company(self, company_name: str) -> Optional[str]:
        """Enhanced company search with multiple strategies"""
        logger.info(f"Searching for company: {company_name}")
        
        # Strategy 1: Direct search
        search_strategies = [
            f"{self.base_url}/search?utf8=✓&query={quote(company_name)}",
            f"{self.base_url}/directory/search?utf8=✓&query={quote(company_name)}",
            f"{self.base_url}/categories?utf8=✓&query={quote(company_name)}"
        ]
        
        for search_url in search_strategies:
            try:
                logger.info(f"Trying search URL: {search_url}")
                soup = self.get_page_content(search_url)
                
                if not soup:
                    continue
                
                # Look for product pages
                product_url = self.find_product_url(soup, company_name)
                if product_url:
                    logger.info(f"Found product URL: {product_url}")
                    return product_url
                
            except Exception as e:
                logger.warning(f"Search strategy failed: {e}")
                continue
        
        # Strategy 2: Try direct URL construction
        company_slug = self.create_company_slug(company_name)
        potential_urls = [
            f"{self.base_url}/directory/31/{company_slug}",
            f"{self.base_url}/p/{company_slug}",
            f"{self.base_url}/directory/{company_slug}",
        ]
        
        for url in potential_urls:
            try:
                logger.info(f"Trying direct URL: {url}")
                soup = self.get_page_content(url)
                if soup and self.is_valid_product_page(soup):
                    logger.info(f"Found valid product page: {url}")
                    return url
            except:
                continue
        
        logger.error(f"Could not find product page for {company_name}")
        return None
    
    def create_company_slug(self, company_name: str) -> str:
        """Create URL slug from company name"""
        slug = company_name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def find_product_url(self, soup: BeautifulSoup, company_name: str) -> Optional[str]:
        """Find product URL from search results"""
        # Multiple selectors for product links
        link_selectors = [
            'a[href*="/p/"]',
            'a[href*="/directory/"]',
            '.search-result a',
            '.product-listing a',
            '.directory-profile-card a'
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True).lower()
                
                if href and company_name.lower() in text:
                    full_url = urljoin(self.base_url, href)
                    if self.is_product_url(full_url):
                        return full_url
        
        return None
    
    def is_product_url(self, url: str) -> bool:
        """Check if URL is a valid product URL"""
        return '/p/' in url or '/directory/' in url
    
    def is_valid_product_page(self, soup: BeautifulSoup) -> bool:
        """Check if the page is a valid product page"""
        indicators = [
            soup.find(string=re.compile(r'reviews?', re.I)),
            soup.select('.reviews, .review, [class*="review"]'),
            soup.find('a', href=re.compile(r'reviews?', re.I))
        ]
        return any(indicators)
    
    def get_reviews_url(self, product_url: str) -> Optional[str]:
        """Get reviews URL from product page"""
        try:
            soup = self.get_page_content(product_url)
            if not soup:
                return None
            
            # Look for reviews link
            reviews_link = soup.find('a', href=re.compile(r'reviews', re.I))
            if reviews_link:
                return urljoin(self.base_url, reviews_link['href'])
            
            # Construct reviews URL
            if '/p/' in product_url:
                product_id = re.search(r'/p/(\d+)', product_url)
                if product_id:
                    return f"{self.base_url}/p/{product_id.group(1)}/reviews"
            
            # Try appending /reviews
            return f"{product_url.rstrip('/')}/reviews"
            
        except Exception as e:
            logger.error(f"Error getting reviews URL: {e}")
            return None
    
    def extract_reviews_from_page(self, soup: BeautifulSoup, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Enhanced review extraction with multiple selectors"""
        reviews = []
        
        # Comprehensive list of review selectors
        review_selectors = [
            '[data-testid*="review"]',
            '.review-item',
            '.review-card',
            '.user-review',
            '.review-container',
            '.review-wrapper',
            '[class*="ReviewCard"]',
            '[class*="review-"]',
            'article[class*="review"]',
            '.testimonial',
            '[data-cy*="review"]'
        ]
        
        review_elements = []
        for selector in review_selectors:
            elements = soup.select(selector)
            if elements:
                review_elements = elements
                logger.info(f"Found {len(elements)} review elements using selector: {selector}")
                break
        
        if not review_elements:
            # Fallback: find elements with review-like content
            review_elements = soup.find_all(['div', 'article', 'section'], 
                                          string=re.compile(r'review|rating|stars', re.I), 
                                          limit=50)
            logger.info(f"Fallback found {len(review_elements)} potential review elements")
        
        for element in review_elements:
            try:
                review = self.extract_single_review(element)
                
                if review:
                    # Date filtering
                    if review.get('date'):
                        review_date = self.parse_date(review['date'])
                        if review_date and start_date <= review_date <= end_date:
                            reviews.append(review)
                            logger.debug(f"Added review from {review['date']}")
                        elif review_date:
                            logger.debug(f"Skipped review from {review['date']} (outside range)")
                    else:
                        # Include reviews without dates
                        reviews.append(review)
                        logger.debug("Added review without date")
                
            except Exception as e:
                logger.warning(f"Error extracting review: {e}")
                continue
        
        return reviews
    
    def extract_single_review(self, element) -> Optional[Dict]:
        """Advanced single review extraction"""
        review = {}
        
        try:
            # Title extraction with multiple strategies
            title_selectors = [
                '[data-testid*="title"], [data-testid*="heading"]',
                '.review-title, .review-header, .review-heading',
                'h1, h2, h3, h4, h5, h6',
                '[class*="title"], [class*="heading"]',
                'strong, b'
            ]
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if len(title_text) > 5 and len(title_text) < 200:  # Reasonable title length
                        review['title'] = title_text
                        break
            
            # Content extraction
            content_selectors = [
                '[data-testid*="content"], [data-testid*="text"]',
                '.review-text, .review-content, .review-description',
                '.user-review-text, .review-body',
                '[class*="content"], [class*="text"], [class*="description"]',
                'p'
            ]
            
            content_parts = []
            for selector in content_selectors:
                content_elements = element.select(selector)
                for elem in content_elements:
                    text = elem.get_text(strip=True)
                    if len(text) > 20 and text not in content_parts:
                        content_parts.append(text)
            
            if content_parts:
                review['description'] = ' '.join(content_parts[:3])  # Limit to first 3 parts
            
            # Date extraction
            date_selectors = [
                '[data-testid*="date"]',
                '.review-date, .date, .posted-date',
                'time, [datetime]',
                '[class*="date"]'
            ]
            
            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    if date_text and len(date_text) > 3:
                        review['date'] = date_text
                        break
                    # Check datetime attribute
                    if date_elem.get('datetime'):
                        review['date'] = date_elem['datetime']
                        break
            
            # Rating extraction
            rating_selectors = [
                '[data-testid*="rating"], [data-testid*="star"]',
                '.rating, .stars, .star-rating',
                '[class*="rating"], [class*="star"]',
                '[aria-label*="star"], [title*="star"]'
            ]
            
            for selector in rating_selectors:
                rating_elem = element.select_one(selector)
                if rating_elem:
                    # Try different rating extraction methods
                    rating = self.extract_rating(rating_elem)
                    if rating:
                        review['rating'] = rating
                        break
            
            # Reviewer information
            reviewer_selectors = [
                '[data-testid*="reviewer"], [data-testid*="author"]',
                '.reviewer-name, .author-name, .user-name',
                '[class*="reviewer"], [class*="author"], [class*="user"]'
            ]
            
            for selector in reviewer_selectors:
                reviewer_elem = element.select_one(selector)
                if reviewer_elem:
                    reviewer_name = reviewer_elem.get_text(strip=True)
                    if reviewer_name and len(reviewer_name) > 1:
                        review['reviewer_name'] = reviewer_name
                        break
            
            # Additional metadata
            self.extract_metadata(element, review)
            
            # Only return if has meaningful content
            if review.get('title') or review.get('description'):
                return review
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in single review extraction: {e}")
            return None
    
    def extract_rating(self, rating_elem) -> Optional[float]:
        """Extract rating from various formats"""
        try:
            # Method 1: Direct text with numbers
            rating_text = rating_elem.get_text(strip=True)
            rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
                if 0 <= rating <= 5:  # Reasonable rating range
                    return rating
            
            # Method 2: Count filled stars
            filled_stars = len(rating_elem.select('.star-filled, .filled, .active, [class*="fill"]'))
            if filled_stars > 0:
                return float(filled_stars)
            
            # Method 3: Check aria-label or title
            for attr in ['aria-label', 'title', 'data-rating']:
                attr_value = rating_elem.get(attr, '')
                if attr_value:
                    rating_match = re.search(r'(\d+(?:\.\d+)?)', attr_value)
                    if rating_match:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            return rating
            
            # Method 4: Check CSS classes for rating
            class_attr = rating_elem.get('class', [])
            if isinstance(class_attr, list):
                class_str = ' '.join(class_attr)
            else:
                class_str = str(class_attr)
            
            rating_match = re.search(r'rating-(\d+)', class_str)
            if rating_match:
                return float(rating_match.group(1))
            
            return None
            
        except Exception:
            return None
    
    def extract_metadata(self, element, review: Dict):
        """Extract additional metadata from review element"""
        try:
            # Company/Job title
            job_selectors = ['.company, .job-title, .position', '[class*="company"], [class*="position"]']
            for selector in job_selectors:
                job_elem = element.select_one(selector)
                if job_elem:
                    job_text = job_elem.get_text(strip=True)
                    if job_text:
                        review['reviewer_company'] = job_text
                        break
            
            # Verified status
            verified_selectors = ['.verified, [class*="verified"]', '[data-verified="true"]']
            for selector in verified_selectors:
                if element.select_one(selector):
                    review['verified'] = True
                    break
            
            # Helpful votes
            helpful_selectors = ['.helpful-count, .votes', '[class*="helpful"], [class*="vote"]']
            for selector in helpful_selectors:
                helpful_elem = element.select_one(selector)
                if helpful_elem:
                    helpful_text = helpful_elem.get_text(strip=True)
                    helpful_match = re.search(r'(\d+)', helpful_text)
                    if helpful_match:
                        review['helpful_votes'] = int(helpful_match.group(1))
                        break
        
        except Exception:
            pass  # Metadata is optional
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Enhanced date parsing with more formats"""
        try:
            date_str = date_str.strip()
            
            # Common formats
            formats = [
                '%B %d, %Y',      # January 1, 2023
                '%b %d, %Y',      # Jan 1, 2023
                '%m/%d/%Y',       # 01/01/2023
                '%d/%m/%Y',       # 01/01/2023 (European)
                '%Y-%m-%d',       # 2023-01-01
                '%d-%m-%Y',       # 01-01-2023
                '%B %Y',          # January 2023
                '%b %Y',          # Jan 2023
                '%Y',             # 2023
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Handle relative dates
            relative_patterns = [
                (r'(\d+)\s*days?\s*ago', lambda x: datetime.now() - timedelta(days=int(x))),
                (r'(\d+)\s*weeks?\s*ago', lambda x: datetime.now() - timedelta(weeks=int(x))),
                (r'(\d+)\s*months?\s*ago', lambda x: datetime.now() - timedelta(days=int(x)*30)),
                (r'(\d+)\s*years?\s*ago', lambda x: datetime.now() - timedelta(days=int(x)*365)),
                (r'yesterday', lambda x: datetime.now() - timedelta(days=1)),
                (r'today', lambda x: datetime.now()),
            ]
            
            date_lower = date_str.lower()
            for pattern, func in relative_patterns:
                match = re.search(pattern, date_lower)
                if match:
                    if match.groups():
                        return func(match.group(1))
                    else:
                        return func(None)
            
            return None
            
        except Exception as e:
            logger.debug(f"Date parsing failed for '{date_str}': {e}")
            return None
    
    def scrape_reviews(self, company_name: str, start_date: str, end_date: str) -> List[Dict]:
        """Main scraping orchestrator"""
        logger.info(f"Starting comprehensive scrape for {company_name}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Mode: {'Selenium' if self.use_selenium else 'CloudScraper/Requests'}")
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Invalid date format. Use YYYY-MM-DD: {e}")
            return []
        
        # Find product page
        product_url = self.search_company(company_name)
        if not product_url:
            return []
        
        # Get reviews URL
        reviews_url = self.get_reviews_url(product_url)
        if not reviews_url:
            logger.error("Could not determine reviews URL")
            return []
        
        logger.info(f"Reviews URL: {reviews_url}")
        
        all_reviews = []
        page = 1
        max_pages = 100
        consecutive_empty_pages = 0
        
        while page <= max_pages and consecutive_empty_pages < 3:
            logger.info(f"Scraping page {page}")
            
            # Construct page URL
            if page == 1:
                page_url = reviews_url
            else:
                separator = '&' if '?' in reviews_url else '?'
                page_url = f"{reviews_url}{separator}page={page}"
            
            try:
                soup = self.get_page_content(page_url)
                if not soup:
                    logger.warning(f"Failed to get content for page {page}")
                    consecutive_empty_pages += 1
                    page += 1
                    continue
                
                # Extract reviews
                page_reviews = self.extract_reviews_from_page(soup, start_dt, end_dt)
                
                if not page_reviews:
                    consecutive_empty_pages += 1
                    logger.info(f"No reviews found on page {page}")
                else:
                    consecutive_empty_pages = 0
                    all_reviews.extend(page_reviews)
                    logger.info(f"Extracted {len(page_reviews)} reviews from page {page}")
                
                # Check for next page indicators
                has_next = self.has_next_page(soup)
                if not has_next:
                    logger.info("No more pages detected")
                    break
                
                page += 1
                
                # Longer delay between pages
                self.random_delay(3, 8)
                
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                consecutive_empty_pages += 1
                page += 1
                continue
        
        logger.info(f"Scraping completed. Total reviews: {len(all_reviews)}")
        return all_reviews
    
    def has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page"""
        next_indicators = [
            'a[aria-label*="Next"]',
            'a[title*="Next"]',
            '.next-page',
            '.pagination-next',
            'a:contains("Next")',
            'a:contains("→")',
            '.page-numbers a:last-child'
        ]
        
        for selector in next_indicators:
            if soup.select(selector):
                return True
        
        return False
    
    def save_to_json(self, reviews: List[Dict], filename: str, company_name: str, start_date: str, end_date: str):
        """Save reviews with comprehensive metadata"""
        metadata = {
            'scraper_info': {
                'version': '2.0',
                'method': 'Selenium' if self.use_selenium else 'CloudScraper',
                'scraped_at': datetime.now().isoformat(),
                'total_reviews': len(reviews)
            },
            'query_info': {
                'company_name': company_name,
                'start_date': start_date,
                'end_date': end_date,
                'source': 'Capterra'
            },
            'reviews': reviews
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Reviews saved to {filename}")
            
            # Also save a simple CSV for easy viewing
            csv_filename = filename.replace('.json', '.csv')
            self.save_to_csv(reviews, csv_filename)
            
        except