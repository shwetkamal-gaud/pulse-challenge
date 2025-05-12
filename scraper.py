import json
import time
import warnings
from datetime import datetime
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from dateutil import parser
import atexit

def start_undetected_chrome():
    options = uc.ChromeOptions()
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
    headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en;q=0.5",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": f"https://www.g2.com/search?utf8=%E2%9C%93&query={company_slug}&source=search",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Sec-GPC": "1",
    "Priority": "u=0, i"
   }
    cookies = {
        "sp": "c3608046-53ff-4607-9e04-9267990ea05b", 
        "cf_clearance": "MoavYucx07sPTSCGtLys6VE96jrrFZjUxaB0SZOBFq0-1738161501-1.2.1.1-NKMmfz_Uyt5LeURV0Q3LIWPhmWsbL1M4texqg6TNQdrOxof4HyS2Ba5KmfcWDQJu4hVlWKXMz8.z5e8Fkl6ii417CrB8G5vFyjqvrK8W.uPdWC1QOduFaUkoz2VOne.H_BN5odDeHhuul0R3T8sgTeO26zL13aZwznUrx3wWG5ueqTDXcZKptAnfwbfAEm6Be.tux97KoQHyQs8l9aMRR_8BciCcrgesX3B7ZSlCH6WdqGNxAz.iaqWtBp1M9SJONW3GlqTCbqHFEeMnsjf0Jvipso08IylB5fPnIP6N8SI", 
        "zfm_cnt_ck_id": "ljtl7vmik681746862716720; zfm_app_3SDj9c=show; zfm_app_9f3XVc=show", "zfm_app_S3V5ee": "show",
        "loginNudgeShown":"true",
        "block%3Asidebar-default":"1",
        "events_distinct_id": "1f3a03b9-6dbb-456c-97f1-ad1e817d0ae8; amplitude_session=1746941295506", "_g2_session_id": "f6052d19f286f865f12be03ab13262ec; _sp_ses.6c8b=*", 
        "datadome": "emKkuFnpa1~vO8JnX5oYhsy~Aqbchm~sKVSfc6Triywf_tJfRc72YvefjOjUAPW2073ykl3sXRPkIg5u_XDa9CxQLb2AYdEvYUQ_CrC3s7C8T1LJiPjrdow9CjtvXLvV",
        "zfm_usr_sess_ck_id":"kcx278qa2lq1746941306011", 
        "AWSALB": "Y2qPoU306FI9PqBRnXLDjkX0Hyna+bSo6eMM1YOr31mTrlSH5kHydFBuMiBHC2eFAnhVvIA6lxSP1eMVAYzmUpbw+uM4RjhyqiBotb43ZeGqhe6tmWkq+ZqvPPuv", 
        "AWSALBCORS": "Y2qPoU306FI9PqBRnXLDjkX0Hyna+bSo6eMM1YOr31mTrlSH5kHydFBuMiBHC2eFAnhVvIA6lxSP1eMVAYzmUpbw+uM4RjhyqiBotb43ZeGqhe6tmWkq+ZqvPPuv", 
        "__cf_bm": "eSv1YjJ0uYAUeuMs84D9oA3T.kodIQ9RZnHKWHkFPYg-1746941306-1.0.1.1-nH3oIRsNtd6hWaWrVXKlzxQFT8zGDmnmOo8LXMNNd4uTyFuYVrcCKQVu.Owf.HkQgK8qhpai5RD_JA6.QM.aZOx4f_JRd7RGKaAXs0rLIZY",
        "_sp_id.6c8b": "f2dacf5a-2a5d-4703-b76d-c2c3a4417a78.1746862714.4.1746941610.1746892431.24de014a-e7da-44f1-9626-161ff149f931.de6f23a1-efeb-4bb5-a348-55ab2a3fb763.591a119f-320f-40e9-9323-5678a0066b6b.1746941302388.7"
    }
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

def scrape_reviews(company_name, start_date, end_date, source):
    company_slug = company_name.lower().replace(" ", "-")
    source_slug = source.lower()

    if source_slug == 'g2':
        url = f"https://www.g2.com/products/{company_slug}/reviews"
    elif source_slug == 'capterra':
        product_url = get_product_id(company_name)
        if not product_url:
            print(f"Could not find Capterra product URL for {company_name}.")
            return []
        url = product_url
        print(url,"url")
    else:
        print("Invalid source! Choose either 'G2' or 'Capterra'.")
        return []

    driver = start_undetected_chrome()
    try:
        driver.get(url)
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        reviews = []

        if source_slug == "g2":
            review_blocks = soup.find_all("div", class_="f-1")
            for review in review_blocks:
                try:
                    title = review.find("a", class_="pjax")
                    description = review.find("p", class_="formatted-text")
                    date_text = review.find("span", class_="x-current-review-date")

                    if not (title and description and date_text):
                        continue

                    review_date = parser.parse(date_text.text.strip())
                    if start_date <= review_date <= end_date:
                        reviews.append({
                            "title": title.text.strip(),
                            "description": description.text.strip(),
                            "date": review_date.strftime("%Y-%m-%d")
                        })
                except Exception as e:
                    print(f"G2 error: {e}")
                    continue

        elif source_slug == "capterra":
            review_blocks = soup.find_all("div", class_="e1xzmg0z c1ofrhif typo-10 mb-6 space-y-4 p-6 lg:space-y-8")
            for review in review_blocks:
                print(review,"review")
                try:
                    name = review.find("span", class_="typo-20 text-neutral-99 font-semibold")
                    title_div = review.find("h3", class_="typo-20 font-semibold")
                    des = review.find("div", class_="!mt-4 space-y-6").find("p")
                    date_span = review.find("div", class_="typo-0 text-neutral-90")
                    review_ratings = review.find("span", class_="e1xzmg0z sr2r3oj")

                    if not (title_div and name and des and date_span):
                        continue

                    review_date = parser.parse(date_span.text.strip())
                    print(start_date <= review_date <= end_date, start_date, review_date, end_date)
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

        return reviews


    except Exception as error:
        print(f"Error while scraping {source}: {str(error)}")
        return []
    finally:
        safe_quit(driver)

def save_to_json(reviews, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(reviews, file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    start_date = parser.parse(input("Enter the start date (YYYY-MM-DD): "))
    end_date = parser.parse(input("Enter the end date (YYYY-MM-DD): "))
    source = input("Enter the source (G2/Capterra): ")

    reviews = scrape_reviews(company_name, start_date, end_date, source)
    save_to_json(reviews, "reviews.json")
    print(f"✅ Scraped {len(reviews)} reviews from {source} for {company_name}.")
