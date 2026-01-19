import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import mysql.connector
from datetime import datetime
import webbrowser


load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME', 'job_radar')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '//your_password_here')

OUT_DIR = "reports"
os.makedirs(OUT_DIR, exist_ok=True)

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user =DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def load_jobs():
    sql ="""
    SELECT
        source,
        adzuna_id,
        title,
        company,
        location,
        url,
        posted_at,
        created_at
    FROM job_postings
    """
    with get_conn() as conn:
        df = pd.read_sql(sql, conn)
    return df

def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce')

    for col in ["title", "company", "location"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    parts = df["location"].str.split(",", n=1, expand=True)
    df["city_raw"] = parts[0].str.strip()
    df["province_raw"] = parts[1].str.strip() if parts.shape[1] > 1 else ""

    df["city"] = df["city_raw"]
    df["province"] = df["province_raw"].fillna("")

    df["geo_level"] = "city"
    df.loc[df["city"].str.match(r"Italia", case=False, na=False), "geo_level"] = "country"
    df.loc[df["province"].str.match(r"^Provincia di ", case=False, na=False), "geo_level"] = "province"

    df["month"] = df["posted_at"].dt.to_period("M").astype(str)

    return df

def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(df)

    distinct_companies = df["company"].replace("", pd.NA).dropna().nunique()   

    last_30 = df[df["posted_at"] >= (pd.Timestamp.now() - pd.Timedelta(days=30))]
    last_7 = df[df["posted_at"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]

    summary = {
        "generated_at": now,
        "total_jobs": total,
        "companies_distinct": int(distinct_companies),
        "jobs_last_30_days": int(len(last_30)),
        "jobs_last_7_days": int(len(last_7)),
        "top_cities": df["city"].value_counts().head(10).to_dict(),
        "top_titles": df["title"].value_counts().head(10).to_dict(),
    }
    return pd.DataFrame([summary])

def top_tables(df: pd.DataFrame):
    top_city = (
    df[df["geo_level"].eq("city")]["city"].value_counts().head(15)
    .rename_axis("city").reset_index(name="count")
    )

    top_province = (
    df.loc[df["geo_level"].eq("province"), "province"].value_counts().head(15)
      .rename_axis("province").reset_index(name="count")
    )


    top_company = (
        df.loc[df["company"].ne(""), "company"].value_counts().head(15)
        .rename_axis("company").reset_index(name="count")
    )

    top_title = (
        df["title"].value_counts().head(15)
        .rename_axis("title").reset_index(name="count")
    )

    by_month = (
        df.loc[df["month"].ne("NaT"), "month"].value_counts()
        .sort_index()
        .rename_axis("month").reset_index(name="count")
    )

    return top_city, top_company, top_title, by_month

def make_charts(df: pd.DataFrame):
    sns.set_theme(style="whitegrid")

    dfx = df.copy()
    dfx["date"] = dfx["posted_at"].fillna(dfx["created_at"])
    dfx = dfx.dropna(subset=["date"])
    dfx = dfx[dfx["date"] >= (pd.Timestamp.now() - pd.Timedelta(days=90))]

    daily = (
        dfx.groupby(dfx["date"].dt.date)
        .size()
        .reset_index()
    )
    daily.columns = ["day", "count"]

    fig1, ax1 = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=daily, x="day", y="count", ax=ax1)
    ax1.set_title("Jobs per day (last 90 days)")
    ax1.set_xlabel("Day")
    ax1.set_ylabel("Job Posts")
    fig1.autofmt_xdate()

    path_trend = os.path.join(OUT_DIR, "trend_90d.png")
    fig1.savefig(path_trend, dpi = 150, bbox_inches='tight')
    plt.close(fig1)

    lazio_mask = dfx["location"].str.contains(r"\bRome\b|\bRoma\b|\bLazio\b", case=False, na=False)
    dfx_lazio = dfx[lazio_mask].copy()
    daily_lazio = (
        dfx_lazio.groupby(dfx_lazio["date"].dt.date)
        .size()
        .reset_index() 
    )
    daily_lazio.columns = ["day", "count"]

    fig2, ax2 = plt.subplots(figsize=(10, 4))
    if len(daily_lazio) > 0:
        sns.lineplot(data=daily_lazio, x="day", y="count", ax=ax2)
    ax2.set_title("Jobs per day (Lazio/Rome),last 90 days)")
    ax2.set_xlabel("Day")
    ax2.set_ylabel("Job Posts")
    fig2.autofmt_xdate()

    path_lazio = os.path.join(OUT_DIR, "trend_lazio_90d.png")
    fig2.savefig(path_lazio, dpi = 150, bbox_inches='tight')
    plt.close(fig2)

    return "trend_90d.png", "trend_lazio_90d.png"

def render_html(summary_df, top_city, top_company, top_title, by_month, trend_img, trend_lazio_img):
    html = f"""
    <html><head><meta charset="utf-8"><title>JobMarketRadar - Market Report</title></head>
    <body>
    <h1>JobMarketRadar - Market Report</h1>
    <h2>Trend (last 90 days)</h2>
    <img src="{trend_img}" style="max-width:100%;height:auto;"/>

    <h2>Lazio / Rome focus (last 90 days)</h2>
    <img src="{trend_lazio_img}" style="max-width:100%;height:auto;"/>

    <h2>Summary</h2>
    {summary_df.to_html(index=False, escape=False)}

    <h2>Top Cities</h2>
    {top_city.to_html(index=False)}

    <h2>Top Companies</h2>
    {top_company.to_html(index=False)}

    <h2>Top Job Titles</h2>
    {top_title.to_html(index=False)}

    <h2>Jobs by Month (posted_at)</h2>
    {by_month.to_html(index=False)}
    </body></html>
    """
    return html

def main():
    df = load_jobs()
    df = clean_jobs(df)


    df.to_csv(os.path.join(OUT_DIR, "report_market.csv"), index=False)

    summary_df = build_summary(df)
    summary_df.to_csv(os.path.join(OUT_DIR, "report_summary.csv"), index=False)

    top_city, top_company, top_title, by_month = top_tables(df)
    trend_img, trend_lazio_img = make_charts(df)

    html = render_html(summary_df, top_city, top_company, top_title, by_month, trend_img, trend_lazio_img)

    with open(os.path.join(OUT_DIR, "report_market.html"), "w", encoding="utf-8") as f:
        f.write(html)

    report_path = os.path.abspath(os.path.join(OUT_DIR, "report_market.html"))
    webbrowser.open_new_tab("file:///" + report_path.replace("\\", "/"))


    print("created reports/report_market.csv, reports/report_summary.csv, reports/report_market.html")

if __name__ == "__main__":
    main()