import json
import time
from bs4 import BeautifulSoup
from dateutil import parser
import atexit
import undetected_chromedriver as uc
from playwright.sync_api import sync_playwright
import random

def start_undetected_chrome():
    options = uc.ChromeOptions()
    USER_AGENTS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    atexit.register(lambda: safe_quit(driver))
    return driver

def safe_quit(driver):
    try:
        driver.quit()
    except Exception:
        pass

def get_product_id(company_name):
    search = f'https://www.capterra.com/search/?query={company_name}'
    driver = start_undetected_chrome()
    try:
        driver.get(search)
        time.sleep(6)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        first_result = soup.find("a", {"data-testid": "star-rating"})
        if first_result:
            return first_result["href"]
        return None
    finally:
        safe_quit(driver) 

def scrape_g2_reviews(company_slug, start_date, end_date):
    url = f"https://www.g2.com/products/{company_slug}/reviews#reviews"
    reviews =[]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(".nested-ajax-loading", timeout=10000)
        reviews = page.query_selector_all(".paper.paper--white.paper--box.mb-2.position-relative.border-bottom ")
        for review in reviews:
            title = review.query_selector("div.m-0.l2[itemprop='name']").inner_text().strip() if review.query_selector("div.m-0.l2[itemprop='name']") else "No Title"
            description = review.query_selector("p.formatted-text").inner_text().strip() if review.query_selector("p.formatted-text") else "No Description"
            date_element = review.query_selector("div.time-stamp.pl-4th.ws-nw meta[itemprop='datePublished']")
            date = date_element.get_attribute("content") if date_element else "Unknown Date"
            reviewer_name = review.query_selector("div.flex.ai-c a.link--header-color").inner_text().strip() if review.query_selector("div.flex.ai-c a.link--header-color") else "Anonymous"
            print(title, description, parser.parse(date), reviewer_name,"alkn")
            if start_date <= parser.parse(date) <= end_date:
                reviews.append({
                            "title": title,
                            "description": description,
                            "date": parser.parse(date),
                            "reviewer_name": reviewer_name,
                })
        browser.close()
    return reviews
def scrape_capterra_reviews(company_name, start_date, end_date):
    product_url = get_product_id(company_name)
    if not product_url:
        print(f"Could not find Capterra product URL for {company_name}.")
        return []
    url = product_url
    driver = start_undetected_chrome()
    reviews = []
    try:
        driver.get(url)
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        review_blocks = soup.find_all("div", class_="e1xzmg0z c1ofrhif typo-10 mb-6 space-y-4 p-6 lg:space-y-8")
        for review in review_blocks:
                try:
                    name = review.find("span", class_="typo-20 text-neutral-99 font-semibold")
                    title_div = review.find("h3", class_="typo-20 font-semibold")
                    des = review.find("div", class_="!mt-4 space-y-6").find("p")
                    date_span = review.find("div", class_="typo-0 text-neutral-90")
                    review_ratings = review.find("span", class_="e1xzmg0z sr2r3oj")

                    if not (title_div and name and des and date_span):
                        continue

                    review_date = parser.parse(date_span.text.strip())
                    if start_date <= review_date <= end_date:
                        reviews.append({
                            "title": title_div.text.strip(),
                            "description": des.text.strip(),
                            "date": review_date.strftime("%Y-%m-%d"),
                            "reviewer_name": name.text.strip(),
                            "rating":review_ratings.text.strip()
                        })
                except Exception as e:
                    print(f"Capterra error: {e}")
                    continue

    except Exception as error:
        print(f"Error while scraping Capterra: {str(error)}")
    finally:
        safe_quit(driver)
    return reviews

def save_to_json(reviews, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(reviews, file, indent=4, ensure_ascii=False)

def main():
    company_name = input("Enter the company name: ")
    start_date = parser.parse(input("Enter the start date (YYYY-MM-DD): "))
    end_date = parser.parse(input("Enter the end date (YYYY-MM-DD): "))
    source = input("Enter the source (G2/Capterra): ").lower()

    if source == "g2":
        company_slug = company_name.lower().replace(" ", "-")
        reviews = scrape_g2_reviews(company_slug, start_date, end_date)
        save_to_json(reviews, "reviews_g2.json")
    elif source == "capterra":
        reviews = scrape_capterra_reviews(company_name, start_date, end_date)
        save_to_json(reviews, "reviews_capterra.json")
    else:
        print("Invalid source! Choose either 'G2' or 'Capterra'.")
        return

    print(f"✅ Scraped {len(reviews)} reviews from {source.capitalize()} for {company_name}.")

if __name__ == "__main__":
    main()
