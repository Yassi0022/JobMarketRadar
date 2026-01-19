import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "it")

if not APP_ID or not APP_KEY:
    raise SystemExit("Mancano ADZUNA_APP_ID / ADZUNA_APP_KEY nel file .env")

WHAT_LIST = ["data analyst", "data scientist"]
RESULTS_PER_PAGE = 50
MAX_PAGES = 300  # alza/abbassa a piacere

all_rows = []

for what in WHAT_LIST:
    print(f"\n=== Query: {what} ===")
    for page in range(1, MAX_PAGES + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": what,
            "results_per_page": RESULTS_PER_PAGE,
            "content-type": "application/json",
        }

        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            print("HTTP:", r.status_code, "Stop.")
            r.raise_for_status()

        data = r.json()
        results = data.get("results", [])

        print(f"page {page}: {len(results)} risultati")

        if not results:
            break

        for j in results:
            all_rows.append({
                "query": what,
                "id": j.get("id"),
                "title": j.get("title"),
                "company": (j.get("company") or {}).get("display_name"),
                "location": (j.get("location") or {}).get("display_name"),
                "created": j.get("created"),
                "redirect_url": j.get("redirect_url"),
            })

        time.sleep(0.2)  # piccolo delay per non martellare l'API

df = pd.DataFrame(all_rows)

# dedup per id (stesso annuncio può uscire in più query)
if not df.empty and "id" in df.columns:
    df = df.drop_duplicates(subset=["id"], keep="first")
df = df.drop(columns=["query"], errors="ignore")


df.to_csv("jobs.csv", index=False)
print(f"\nOK: salvati {len(df)} annunci unici in jobs.csv")