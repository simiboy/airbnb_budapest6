import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

# URL
url = "https://www.govcenter.hu/szallashely/Public/SzallashelyList.aspx?ltip=true&onk_id=432"

# Fetch page
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# Get all tables
tables = soup.find_all("table")
target_table = tables[1]  # second table

# Define headers manually to match 15 columns
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

# Extract table rows
rows = []
for tr in target_table.find_all("tr")[3:]:  # skip first 3 rows (title + header)
    cols = tr.find_all("td")
    if len(cols) == 0:
        continue
    row = [col.get_text(strip=True) for col in cols]
    rows.append(row)

# Create DataFrame
df = pd.DataFrame(rows, columns=headers)

# Create data folder if not exists
os.makedirs("data", exist_ok=True)

# Save CSV with current date
today = datetime.today().strftime("%Y-%m-%d")
filename = f"data/{today}.csv"
df.to_csv(filename, index=False, encoding="utf-8-sig")

print(f"Data saved to {filename}")
