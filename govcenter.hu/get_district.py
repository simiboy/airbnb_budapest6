import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time

# URL template
url_template = "https://www.govcenter.hu/szallashely/Public/SzallashelyList.aspx?ltip=true&onk_id={onk_id}"

# Manual headers
headers = [
    "Üzemeltetési engedély száma",
    "Szálláshely-szolgáltató neve, címe",
    "Szálláshely-szolgáltató adószáma",
    "Szálláshely-szolgáltató statisztikai száma",
    "Szálláshely neve",
    "Szálláshely címe, helyrajzi száma",
    "Szálláshely típusa",
    "Minőségi fokozat",
    "NTAK nyilvántartási szám",
    "Szobák száma",
    "Ágyak száma",
    "Engedély dátuma",
    "Szálláshely ideiglenes bezárás",
    "Szálláshely megszűnés",
    "Engedélyben foglalt korlátok"
]

budapest_onk_ids = set()
all_addresses = []

# Loop through potential onk_ids
for onk_id in range(1, 1001):
    url = url_template.format(onk_id=onk_id)
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 2:
            continue
        table = tables[1]

        rows = table.find_all("tr")[3:]  # skip first 3 rows
        for tr in rows:
            cols = tr.find_all("td")
            if len(cols) < 15:
                continue
            szallashely_cime = cols[5].get_text(strip=True)
            postal_code = szallashely_cime[:4]  # first 4 chars
            if postal_code.startswith("1"):  # Budapest
                budapest_onk_ids.add(onk_id)
                all_addresses.append(szallashely_cime)
        time.sleep(0.2)  # polite pause
    except Exception as e:
        print(f"Error with onk_id {onk_id}: {e}")
        continue

# Save onk_ids
os.makedirs("data", exist_ok=True)
today = datetime.today().strftime("%Y-%m-%d")
onk_filename = f"data/budapest_onk_ids_{today}.csv"
pd.DataFrame(sorted(budapest_onk_ids), columns=["onk_id"]).to_csv(onk_filename, index=False, encoding="utf-8-sig")

# Save addresses
addr_filename = f"data/budapest_addresses_{today}.csv"
pd.DataFrame(all_addresses, columns=["szallashely_cime"]).to_csv(addr_filename, index=False, encoding="utf-8-sig")

print(f"Found {len(budapest_onk_ids)} Budapest onk_ids.")
print(f"Addresses saved to {addr_filename}")
print(f"Onk_ids saved to {onk_filename}")
