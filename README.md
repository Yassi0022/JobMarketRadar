# JobMarketRadar

A personal end-to-end job market radar built with **Java + Python**.

It:
1) Fetches job postings from the Adzuna API (Python),
2) Upserts them into a MySQL database (Java),
3) Generates an HTML/CSV report with charts (Python).

## Tech stack
- Java (Maven), JDBC
- Python (requests, pandas, mysql-connector, matplotlib, seaborn)
- MySQL

## Project structure (main files)
- `my-app/src/main/java/com/mycompany/app/App.java` → orchestrates the full pipeline
- `my-app/src/main/python/adzuna_ingest.py` → fetches data from Adzuna and writes `jobs.csv`
- `my-app/src/main/python/market_report.py` → reads from MySQL and generates the report

## Setup
### 1 Environment variables 
Create a `.env` file in:
`my-app/src/main/python/.env`

You can use `.env.example` as a template. (API keys and DB credentials are not committed.) 

Required variables:
- `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ADZUNA_COUNTRY`
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

### 2 Python virtual environment
From `my-app/src/main/python`:

```bash
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

### 3 MySQL
Create a MySQL database and the `job_postings` table (must include a UNIQUE key on `adzuna_id` for the upsert).

## Run (one command)
From the repository root:

```bash
mvn -f my-app/pom.xml exec:java -Dexec.mainClass="com.mycompany.app.App"

## Output
The report is generated in:
my-app/src/main/python/reports/report_market.html

