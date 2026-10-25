# JobMarketRadar

JobMarketRadar collects job postings from Adzuna, stores them in MySQL, and generates HTML and CSV market reports.

*Static demo:* my-app/demo/report.html (uses fictional data, no Adzuna credentials or MySQL needed).

## Pipeline

1. Fetch job postings from Adzuna for the configured search queries
2. Write the postings to an intermediate jobs.csv file
3. Import the CSV into the MySQL job_postings table
4. Generate HTML, CSV, and chart outputs from the database

The Java app orchestrates the Python scripts and imports the data; Python handles Adzuna ingestion and report generation

## Requirements

- Java 17, Maven, Python 3, MySQL 8
- Adzuna API credentials (ADZUNA_APP_ID and ADZUNA_APP_KEY)

Python dependencies: my-app/src/main/python/requirements.txt

## Configuration

Python loads config from my-app/src/main/python/.env, create it from the committed .env.example and set:

ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
DB_HOST=localhost
DB_PORT=3306
DB_NAME=jobmarket_db
DB_USER=root
DB_PASSWORD=your_mysql_password

Never commit .env or put credentials in source code

### Java and .env

Python loads .env with python-dotenv; Java does NOT load that file, DB.java reads DB_* from the process environment via System.getenv(). Defaults: localhost:3306, jobmarket_db, root, empty password. If your MySQL settings differ, export the DB_* variables in the terminal before running Maven, with the same values as .env

## Setup

1. Start MySQL 8 and apply the schema from the repo root:

macOS/Linux:
mysql -u root -p < my-app/schema.sql

Windows PowerShell:
Get-Content .\my-app\schema.sql | mysql -u root -p

2. Create .env:

macOS/Linux:
cp my-app/src/main/python/.env.example my-app/src/main/python/.env

Windows:
Copy-Item .\my-app\src\main\python\.env.example .\my-app\src\main\python\.env

Edit it with your Adzuna and MySQL values

3. Create the venv and install dependencies:

macOS/Linux:
cd my-app/src/main/python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ../../../../

Windows:
Set-Location .\my-app\src\main\python
py -3 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
Set-Location ..\..\..\..

## Run the pipeline

From the repo root, export the DB_* variables first if they differ from the defaults, then:

macOS/Linux:
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_NAME="jobmarket_db"
export DB_USER="root"
export DB_PASSWORD="your_mysql_password"
mvn -f my-app/pom.xml exec:java -Dexec.mainClass="com.mycompany.app.App"

Windows:
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "jobmarket_db"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your_mysql_password"
mvn -f my-app/pom.xml exec:java "-Dexec.mainClass=com.mycompany.app.App"

## Python interpreter selection

App.java picks the Python used to run the scripts: Windows default .venv/Scripts/python.exe, macOS/Linux .venv/bin/python. Set PYTHON_EXE to override. If the chosen interpreter is missing, create the venv at the default location or set PYTHON_EXE to a valid one

## Generated files

Output goes to my-app/src/main/python/reports/: report_market.html, report_market.csv, report_summary.csv, trend_90d.png, trend_lazio_90d.png. The ingestion script also writes jobs.csv

## Run Maven tests

mvn -f my-app/pom.xml test