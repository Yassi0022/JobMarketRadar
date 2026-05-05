# 📡 JobMarketRadar

An end-to-end **job market data pipeline** built with Java + Python that collects job postings from the Adzuna API, stores them in MySQL, and generates automated HTML/CSV reports to monitor labor market demand, roles, and trends.

Built as a personal tool to analyze which tech profiles are most requested and how the job market evolves over time.

---

## 🔄 Pipeline Architecture

```
Adzuna API
    │
    ▼
adzuna_ingest.py          # Python: HTTP fetch → jobs.csv
    │
    ▼
App.java                  # Java: reads jobs.csv → batch upsert into MySQL (JDBC)
    │                     # ON DUPLICATE KEY UPDATE on adzuna_id — idempotent
    ▼
market_report.py          # Python: reads from MySQL → HTML report + charts + CSV
    │
    ▼
reports/
  ├── report_market.html   # Full interactive report (auto-opens in browser)
  ├── report_market.csv    # Full cleaned dataset
  └── report_summary.csv   # Aggregated KPIs
```

The pipeline is **orchestrated by a single Java entry point** (`App.java`) that invokes the two Python scripts as subprocesses via `ProcessBuilder`. One Maven command runs the full flow.

---

## 📊 Report Output

`market_report.py` reads directly from MySQL and produces:

- **Trend charts** — jobs posted per day over the last 90 days (national + Lazio/Rome focus)
- **Top Cities** — top 15 cities by job volume (city-level only, provinces and "Italia" separated)
- **Top Companies** — top 15 hiring companies
- **Top Job Titles** — top 15 most frequent roles
- **Jobs by Month** — posting volume over time by `posted_at`
- **Summary KPIs** — total jobs, distinct companies, jobs in last 7 and 30 days

All tables and charts are embedded in a single `report_market.html` that opens automatically in the browser after each run.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Java 21, Maven, `ProcessBuilder` (subprocess invocation) |
| Data Ingestion | Python, `requests`, Adzuna REST API → `jobs.csv` |
| Storage | MySQL 8 — JDBC batch upsert, `ON DUPLICATE KEY UPDATE` |
| CSV Parsing | `opencsv` — `CSVReaderBuilder` with header skip |
| Reporting | Python, `pandas`, `matplotlib`, `seaborn`, `mysql-connector` |
| Config | `.env` (python-dotenv), `.env.example` committed |

---

## 📁 Project Structure

```
JobMarketRadar/
└── my-app/
    ├── pom.xml
    └── src/main/
        ├── java/com/mycompany/app/
        │   ├── App.java              # Pipeline orchestrator
        │   └── DB.java               # JDBC connection helper
        └── python/
            ├── adzuna_ingest.py      # API fetch → jobs.csv
            ├── market_report.py      # MySQL → HTML/CSV report + charts
            ├── requirements.txt
            ├── .env.example
            └── reports/             # Generated output (gitignored)
                ├── report_market.html
                ├── report_market.csv
                ├── report_summary.csv
                ├── trend_90d.png
                └── trend_lazio_90d.png
```

---

## ⚙️ Setup

### 1. Environment variables

Create `my-app/src/main/python/.env` from `.env.example`:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=it          # e.g. it, gb, us

DB_HOST=localhost
DB_PORT=3306
DB_NAME=jobmarket_db
DB_USER=your_user
DB_PASSWORD=your_password
```

> API keys and DB credentials are never committed.

### 2. Python virtual environment

```bash
cd my-app/src/main/python
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. MySQL

Create the database and the `job_postings` table with a `UNIQUE` constraint on `adzuna_id`:

```sql
CREATE TABLE job_postings (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    source     VARCHAR(50),
    adzuna_id  BIGINT UNIQUE,
    title      VARCHAR(255),
    company    VARCHAR(255),
    location   VARCHAR(255),
    url        TEXT,
    posted_at  DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ▶️ Run

One command from the repository root runs the full pipeline:

```bash
mvn -f my-app/pom.xml exec:java -Dexec.mainClass="com.mycompany.app.App"
```

The HTML report opens automatically in the browser when done.

---

## 💡 Key Design Decisions

**Java as orchestrator, Python for data work.**
`App.java` uses `ProcessBuilder` with `inheritIO()` to invoke the Python scripts as subprocesses, streaming their stdout/stderr live to the terminal. Java handles the upsert with full JDBC transaction control (`setAutoCommit(false)` + `commit()`); Python handles API calls and visualization where pandas/matplotlib/seaborn are the natural fit.

**Batch upsert for performance and idempotency.**
Records are inserted in batches of 500 via `PreparedStatement.addBatch()`. The `ON DUPLICATE KEY UPDATE` clause on `adzuna_id` makes the pipeline idempotent — running it daily updates existing postings without duplicates.

**Defensive CSV parsing.**
Each row is validated before insertion: rows with fewer than 6 fields are skipped, `adzuna_id` is parsed as `Long`, and `posted_at` is parsed from ISO-8601 `OffsetDateTime` with graceful fallback to `NULL`. Invalid row counts are logged at the end.

**Geo-level classification in reporting.**
`market_report.py` splits the `location` field and classifies each posting as `city`, `province`, or `country` level, filtering out "Italia" entries from city rankings to avoid noise in geographic analysis.

---

## 👤 Author

**Yassine Hatouf** · [GitHub](https://github.com/Yassi0022) · [LinkedIn](https://linkedin.com/in/yassine-hatouf)
