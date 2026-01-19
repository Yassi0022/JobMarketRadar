# JobMarketRadar

Tool personale (Java + Python) che:
1) scarica job postings da Adzuna API,
2) fa upsert su MySQL,
3) genera report HTML/CSV con grafici.

## Setup
- Crea `.env` a partire da `.env.example` in `my-app/src/main/python/`.
- Crea venv e installa requirements:
  - `cd my-app/src/main/python`
  - `py -m venv .venv`
  - `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`

## Run
- `cd JobMarketRadar`
- `mvn -f my-app/pom.xml exec:java -Dexec.mainClass="com.mycompany.app.App"`

Output: `my-app/src/main/python/reports/report_market.html`
