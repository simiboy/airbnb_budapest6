from booking_com import scrape as booking_scrape
from ingatlan_com import scrape as ingatlan_scrape
import generate_dashboard

#booking_scrape.main()
#ingatlan_scrape.main()
generate_dashboard.main()


# ---------------- GIT AUTOMATION ----------------
import subprocess
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m-%d")
commit_message = f"successful_scrape_{current_date}"

subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", commit_message], check=True)
subprocess.run(["git", "push"], check=True)