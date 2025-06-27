
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# start a configured Chrome browser
options = Options()
options.headless = True  # hide GUI
options.add_argument("--window-size=1920,1080")  # set window size to native GUI size
options.add_argument("start-maximized")  # ensure window is full-screen
driver = webdriver.Chrome(options=options)

# scrape the reviews page
driver.get("https://www.capterra.in/software/135003/slack")
# wait up to 5 seconds for element to appear 
element = WebDriverWait(driver=driver, timeout=5).until(
    # EC.presence_of_element_located((By.CSS_SELECTOR, '.review'))
    EC.presence_of_element_located((By.CSS_SELECTOR, '.container'))
)
# retrieve the resulting HTML and parse it for datao
html = driver.page_source
print(html)



# from playwright.sync_api import sync_playwright

# # Start Playwright
# with sync_playwright() as p:
#     # Launch a headless browser
#     browser = p.chromium.launch(headless=True)
#     # Open a new browser tab
#     page = browser.new_page()
#     page.set_viewport_size({"width": 1920, "height": 1080})  # Set window size
    
#     # scrape the reviews page
#     # page.goto("https://web-scraping.dev/reviews")
#     page.goto("https://www.capterra.in/reviews/135003/slack")
#     # wait up to 5 seconds for element to appear 
#     page.wait_for_selector('.container', timeout=5000)
    
#     # Retrieve the HTML content
#     html = page.content()
#     print(html)
    
#     # Close the browser
#     browser.close()


# driver.close()