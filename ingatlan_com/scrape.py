import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
import csv
import time
import random
import sys
import os

# ---------------- PATHS FIXED ----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(OUTPUT_DIR, f"{date.today()}.csv")

BASE_URL = "https://ingatlan.com/lista/kiado+lakas+budapest?page="
SLEEP_MIN, SLEEP_MAX = 3.0, 7.0

# Proxy list (example: "http://IP:PORT")
PROXIES = [
    # "http://123.45.67.89:8080",
]

# ---------------- DRIVER SETUP ----------------
def get_driver(proxy=None):
    options = uc.ChromeOptions()
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    driver = uc.Chrome(options=options, version_main=141, headless=False)
    return driver

# ---------------- STATE MANAGEMENT ----------------
def make_state():
    return {
        "driver": None,
        "cookies_accepted": False,
        "max_pages": 1,
        "start_time": time.time(),
        "proxy_index": 0,
    }

# ---------------- COOKIE HANDLER ----------------
def accept_cookies(state):
    if state["cookies_accepted"]:
        return
    driver = state["driver"]
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
        )
        time.sleep(1.2)
        btn.click()
        state["cookies_accepted"] = True
        print("✅ Accepted cookies.")
        time.sleep(1.2)
    except Exception:
        pass

# ---------------- MAX PAGES ----------------
def set_max_pages(state):
    driver = state["driver"]
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".text-gray-200, .pagination"))
        )
        elems = driver.find_elements(By.CSS_SELECTOR, ".text-gray-200")
        if elems and "/" in elems[0].text:
            state["max_pages"] = int(elems[0].text.split("/")[1].strip())
        else:
            pag_links = driver.find_elements(By.CSS_SELECTOR, "ul.pagination li a")
            page_nums = [int(a.text) for a in pag_links if a.text.isdigit()]
            if page_nums:
                state["max_pages"] = max(page_nums)
        print(f"📄 Total pages: {state['max_pages']}")
    except Exception:
        state["max_pages"] = 1
        print("⚠️ Could not detect max pages, defaulting to 1.")

# ---------------- PROGRESS BAR ----------------
def print_progress(current_page, state):
    elapsed = time.time() - state["start_time"]
    avg_time_per_page = elapsed / current_page if current_page else 0
    remaining_pages = max(state["max_pages"] - current_page, 0)
    est_remaining = avg_time_per_page * remaining_pages

    bar_length = 30
    progress = current_page / state["max_pages"] if state["max_pages"] > 0 else 0
    filled_length = int(bar_length * progress)
    bar = "▓" * filled_length + "░" * (bar_length - filled_length)

    sys.stdout.write(
        f"\r📊 Page {current_page}/{state['max_pages']} | {bar} {progress*100:5.1f}% | "
        f"⏱️ Elapsed: {elapsed/60:.1f} min | ⌛ ETA: {est_remaining/60:.1f} min"
    )
    sys.stdout.flush()

# ---------------- CLOUDFLARE CHECK ----------------
def is_cloudflare_challenge(state):
    driver = state["driver"]
    try:
        url = driver.current_url or ""
        title = (driver.title or "").lower()
        body_text = (driver.find_element(By.TAG_NAME, "body").text or "").lower()[:1200]
    except Exception:
        url = title = body_text = ""
    if "/cdn-cgi/" in url:
        return True
    if "just a moment" in title or "checking your browser" in title:
        return True
    if "checking your browser before accessing" in body_text:
        return True
    return False

# ---------------- SIMULATE HUMAN BROWSING ----------------
def simulate_browsing_behavior(state):
    driver = state["driver"]
    try:
        for _ in range(random.randint(3, 7)):
            scroll = random.randint(200, 800) * random.choice([1, -1])
            driver.execute_script(f"window.scrollBy(0, {scroll});")
            time.sleep(random.uniform(0.5, 2.0))
    except Exception:
        pass

# ---------------- CLOUDFLARE HANDLER ----------------
def handle_cloudflare(state, page_number, max_retries=5):
    driver = state["driver"]
    retry = 0
    backoff = 5
    while retry < max_retries:
        print(f"🛡️ Cloudflare detected on page {page_number}. Waiting {backoff}s before retry...")
        time.sleep(backoff)
        driver.refresh()
        time.sleep(random.uniform(2, 4))
        if not is_cloudflare_challenge(state):
            print("✅ Cloudflare cleared after backoff.")
            return True
        retry += 1
        backoff *= 2
    print("❌ Cloudflare still active after retries.")
    return False

# ---------------- SCRAPE PAGE ----------------
def scrape_page(page_number, state):
    driver = state["driver"]
    url = f"{BASE_URL}{page_number}"
    print(f"\n🔗 Loading page {page_number}: {url}")
    driver.get(url)

    if is_cloudflare_challenge(state):
        cleared = handle_cloudflare(state, page_number)
        if not cleared:
            return []

    if not state["cookies_accepted"]:
        accept_cookies(state)

    if not is_cloudflare_challenge(state):
        simulate_browsing_behavior(state)

    if page_number == 1:
        set_max_pages(state)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".listing-card"))
        )
    except Exception:
        print("⚠️ No listings found after waiting.")
        return []

    listings = driver.find_elements(By.CSS_SELECTOR, ".listing-card")
    listings_data = []

    for listing in listings:
        data = {}
        try:
            data["price"] = listing.find_element(By.CSS_SELECTOR, ".listing-card-content .me-2").text.strip()
        except: data["price"] = None
        try:
            data["location"] = listing.find_element(By.CSS_SELECTOR, ".d-block.fs-7.text-gray-900").text.strip()
        except: data["location"] = None
        details = listing.find_elements(By.CSS_SELECTOR, ".w-100.mt-3 .fs-6")
        data["alapterulet"] = details[0].text.strip() if len(details) > 0 else None
        data["szobak"] = details[1].text.strip() if len(details) > 1 else None
        data["erkely"] = details[2].text.strip() if len(details) > 2 else None
        data["page"] = page_number
        listings_data.append(data)

    print(f"✅ Collected {len(listings_data)} listings from page {page_number}.")
    return listings_data

# ---------------- MAIN LOOP ----------------
def main():
    state = make_state()
    proxy = PROXIES[0] if PROXIES else None
    state["driver"] = get_driver(proxy)
    print("✅ Launched undetected Chrome visibly — starting scrape...")

    all_data = []
    page_number = 1

    while True:
        if PROXIES and page_number % 10 == 0:
            state["proxy_index"] = (state["proxy_index"] + 1) % len(PROXIES)
            state["driver"].quit()
            state["driver"] = get_driver(PROXIES[state["proxy_index"]])
            print(f"🔄 Switched to new proxy: {PROXIES[state['proxy_index']]}")

        page_data = scrape_page(page_number, state)

        if page_data:
            all_data.extend(page_data)
            print_progress(page_number, state)
            page_number += 1
        else:
            print(f"\n❌ Page {page_number} blocked or empty.")
            user_input = input("Type 'y' to quit, 'r' to retry, or Enter to skip: ").strip().lower()
            if user_input == "y":
                break
            elif user_input == "r":
                time.sleep(random.uniform(3, 7))
                continue
            else:
                page_number += 1

        if page_number > state["max_pages"]:
            print("\n✅ Reached last page.")
            break

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    if all_data:
        print(f"\n💾 Saving {len(all_data)} listings to {OUTPUT_CSV}...")
        fieldnames = ["page", "price", "location", "alapterulet", "szobak", "erkely"]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)
        print("✅ CSV saved successfully.")

    state["driver"].quit()
    print("🚀 Scraping complete.")

# ---------------- SAFE IMPORT ----------------
if __name__ == "__main__":
    main()
