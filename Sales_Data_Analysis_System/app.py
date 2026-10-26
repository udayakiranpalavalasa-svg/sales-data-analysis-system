"""
Sales Data Analysis System
Data Analysis Essentials Cornerstone Project - Dept. of AI & ML

Flask + JSON API backend powering a single-page, Chart.js-driven dashboard
(templates/index.html). Pandas/NumPy do all the analysis; the browser
renders live, filterable charts instead of static images.
"""
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATA_FILE = BASE_DIR / "Sales_Data.csv"
UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "sales-data-analysis-demo-key"

REQUIRED_COLUMNS = [
    "Order ID", "Product", "Quantity Ordered", "Price Each",
    "Order Date", "Purchase Address",
]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# US Census region grouping, derived from the state in Purchase Address
# (the raw dataset has no Region column - this is an enhancement on top
# of it, same as the estimated cost ratios below).
STATE_TO_REGION = {
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast", "NH": "Northeast",
    "RI": "Northeast", "VT": "Northeast", "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast",
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest", "OH": "Midwest", "WI": "Midwest",
    "IA": "Midwest", "KS": "Midwest", "MN": "Midwest", "MO": "Midwest", "NE": "Midwest",
    "ND": "Midwest", "SD": "Midwest",
    "DE": "South", "FL": "South", "GA": "South", "MD": "South", "NC": "South", "SC": "South",
    "VA": "South", "DC": "South", "WV": "South", "AL": "South", "KY": "South", "MS": "South",
    "TN": "South", "AR": "South", "LA": "South", "OK": "South", "TX": "South",
    "AZ": "West", "CO": "West", "ID": "West", "MT": "West", "NV": "West", "NM": "West",
    "UT": "West", "WY": "West", "AK": "West", "CA": "West", "HI": "West", "OR": "West", "WA": "West",
}

# Estimated cost-to-price ratio per product category, used ONLY for the
# Profit Analysis enhancement module (the raw dataset has no cost column).
DEFAULT_COST_RATIO = 0.70
PRODUCT_COST_RATIO = {
    "USB-C Charging Cable": 0.60, "Lightning Charging Cable": 0.60,
    "AAA Batteries (4-pack)": 0.55, "AA Batteries (4-pack)": 0.55,
    "Wired Headphones": 0.62, "Apple Airpods Headphones": 0.68, "Bose SoundSport Headphones": 0.65,
    "20in Monitor": 0.74, "27in FHD Monitor": 0.75, "27in 4K Gaming Monitor": 0.76,
    "34in Ultrawide Monitor": 0.76, "Flatscreen TV": 0.78,
    "iPhone": 0.83, "Google Phone": 0.82, "Vareebadd Phone": 0.80,
    "LG Washing Machine": 0.74, "LG Dryer": 0.74,
    "Macbook Pro Laptop": 0.80, "ThinkPad Laptop": 0.79,
}


# ============================================================
# Data loading / cleaning / preprocessing
# ============================================================
def load_data():
    df = pd.read_csv(DATA_FILE)
    if "Unnamed: 0" in df.columns:
        df = df.drop("Unnamed: 0", axis=1)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    return df[REQUIRED_COLUMNS].copy()


def _extract_city_state(address):
    parts = str(address).split(",")
    if len(parts) >= 3:
        city = parts[1].strip()
        state = parts[2].strip().split(" ")[0]
        return city, state
    return "Unknown", "XX"


def clean_data(df):
    cleaned = df.copy()
    cleaned = cleaned.dropna(how="all")

    raw_dates = cleaned["Order Date"]
    parsed = pd.to_datetime(raw_dates, format="%m/%d/%y %H:%M", errors="coerce")
    still_missing = parsed.isna()
    if still_missing.any():
        parsed.loc[still_missing] = pd.to_datetime(raw_dates[still_missing], errors="coerce")
    cleaned["Order Date"] = parsed
    cleaned = cleaned.dropna(subset=["Order ID", "Order Date"])

    cleaned["Quantity Ordered"] = pd.to_numeric(cleaned["Quantity Ordered"], errors="coerce")
    cleaned["Price Each"] = pd.to_numeric(cleaned["Price Each"], errors="coerce")
    cleaned["Quantity Ordered"] = cleaned["Quantity Ordered"].fillna(cleaned["Quantity Ordered"].median())
    cleaned["Price Each"] = cleaned["Price Each"].fillna(cleaned["Price Each"].mean())

    cleaned["Product"] = cleaned["Product"].fillna("Unknown").astype(str).str.strip()
    cleaned["Purchase Address"] = cleaned["Purchase Address"].fillna("Unknown, Unknown, XX 00000")
    cleaned["Order ID"] = cleaned["Order ID"].astype(str).str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.drop_duplicates(subset=["Order ID"], keep="first")

    cleaned["Sales"] = (cleaned["Quantity Ordered"] * cleaned["Price Each"]).round(2)
    cleaned["Month"] = cleaned["Order Date"].dt.month
    cleaned["Hour"] = cleaned["Order Date"].dt.hour

    city_state = cleaned["Purchase Address"].apply(_extract_city_state)
    cleaned["City"] = city_state.apply(lambda t: f"{t[0]} ({t[1]})")
    cleaned["State"] = city_state.apply(lambda t: t[1])
    cleaned["Region"] = cleaned["State"].map(STATE_TO_REGION).fillna("Other")

    cost_ratio = cleaned["Product"].map(PRODUCT_COST_RATIO).fillna(DEFAULT_COST_RATIO)
    cleaned["EstUnitCost"] = (cleaned["Price Each"] * cost_ratio).round(2)
    cleaned["Profit"] = ((cleaned["Price Each"] - cleaned["EstUnitCost"]) * cleaned["Quantity Ordered"]).round(2)

    cleaned = cleaned.sort_values("Order Date").reset_index(drop=True)
    return cleaned


def missing_summary(raw):
    return {col: int(raw[col].isna().sum()) for col in REQUIRED_COLUMNS}


def get_cleaned():
    return clean_data(load_data())


def apply_filters(df, args):
    filtered = df.copy()
    search = (args.get("search") or "").strip().lower()
    region = args.get("region") or "All"
    product = args.get("product") or "All"
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if region and region != "All":
        filtered = filtered[filtered["Region"] == region]
    if product and product != "All":
        filtered = filtered[filtered["Product"] == product]
    if date_from:
        filtered = filtered[filtered["Order Date"] >= pd.to_datetime(date_from)]
    if date_to:
        filtered = filtered[filtered["Order Date"] <= pd.to_datetime(date_to) + pd.Timedelta(days=1)]
    if search:
        mask = (
            filtered["Order ID"].str.lower().str.contains(search)
            | filtered["Product"].str.lower().str.contains(search)
            | filtered["City"].str.lower().str.contains(search)
            | filtered["Region"].str.lower().str.contains(search)
        )
        filtered = filtered[mask]
    return filtered


def filtered_df():
    cleaned = get_cleaned()
    df = apply_filters(cleaned, request.args)
    return cleaned, df


# ============================================================
# Analysis helpers -> plain dict/list JSON payloads
# ============================================================
def series_payload(series, sort_desc=True, limit=None):
    s = series.sort_values(ascending=not sort_desc) if sort_desc else series
    if limit:
        s = s.head(limit)
    return {"labels": [str(k) for k in s.index.tolist()], "values": [round(float(v), 2) for v in s.values]}


def compute_trend(df, granularity):
    freq_map = {"day": "D", "week": "W", "month": "ME"}
    freq = freq_map.get(granularity, "D")
    if df.empty:
        return {"labels": [], "values": []}
    trend = df.set_index("Order Date").resample(freq)["Sales"].sum()
    fmt = "%Y-%m-%d" if granularity in ("day", "week") else "%b %Y"
    return {"labels": [d.strftime(fmt) for d in trend.index], "values": [round(float(v), 2) for v in trend.values]}


def compute_histogram(df, bins=12):
    if df.empty:
        return {"labels": [], "values": []}
    counts, edges = np.histogram(df["Sales"], bins=bins)
    labels = [f"${int(edges[i])}-{int(edges[i+1])}" for i in range(len(edges) - 1)]
    return {"labels": labels, "values": [int(c) for c in counts]}


def linear_forecast(df, periods=3):
    if df.empty:
        return {"actual": {"labels": [], "values": []}, "forecast": {"labels": [], "values": []}, "trend": "flat"}
    monthly = df.set_index("Order Date").resample("ME")["Sales"].sum()
    if len(monthly) < 2:
        return {
            "actual": {"labels": [d.strftime("%b %Y") for d in monthly.index], "values": [round(float(v), 2) for v in monthly.values]},
            "forecast": {"labels": [], "values": []},
            "trend": "flat",
        }
    x = np.arange(len(monthly))
    y = monthly.values
    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(len(monthly), len(monthly) + periods)
    future_values = np.clip(slope * future_x + intercept, 0, None)
    future_dates = pd.date_range(monthly.index[-1] + pd.offsets.MonthEnd(1), periods=periods, freq="ME")
    trend_direction = "upward" if slope > 0 else "downward" if slope < 0 else "flat"
    return {
        "actual": {"labels": [d.strftime("%b %Y") for d in monthly.index], "values": [round(float(v), 2) for v in monthly.values]},
        "forecast": {"labels": [d.strftime("%b %Y") for d in future_dates], "values": [round(float(v), 2) for v in future_values]},
        "trend": trend_direction,
    }


def generate_insights(df):
    if df.empty:
        return ["No data available for the selected filters."]
    insights = []
    region_sales = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
    product_sales = df.groupby("Product")["Sales"].sum().sort_values(ascending=False)

    top_region = region_sales.index[0]
    top_region_share = region_sales.iloc[0] / region_sales.sum() * 100
    insights.append(f"{top_region} is the top-performing region, contributing {top_region_share:.1f}% of total sales.")

    top_product = product_sales.index[0]
    insights.append(f"{top_product} is the best-selling product, generating ${product_sales.iloc[0]:,.0f} in sales.")

    avg_order = df["Sales"].mean()
    insights.append(f"The average order value is ${avg_order:,.2f} across {df['Order ID'].nunique()} orders.")

    monthly = df.set_index("Order Date").resample("ME")["Sales"].sum()
    if len(monthly) >= 2:
        change = (monthly.iloc[-1] - monthly.iloc[-2]) / max(monthly.iloc[-2], 1) * 100
        direction = "increased" if change >= 0 else "decreased"
        insights.append(f"Sales {direction} by {abs(change):.1f}% in the most recent month versus the previous one.")

    hourly = df.groupby("Hour")["Sales"].sum()
    if len(hourly):
        best_hour = int(hourly.idxmax())
        insights.append(f"Order volume peaks around {best_hour}:00 — a good window to schedule promotions or ads.")

    margin = (df["Profit"].sum() / df["Sales"].sum() * 100) if df["Sales"].sum() else 0
    insights.append(f"Estimated overall profit margin is {margin:.1f}% across the selected data.")

    return insights


# ============================================================
# Page route
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# JSON API
# ============================================================
@app.route("/api/meta")
def api_meta():
    cleaned = get_cleaned()
    return jsonify({
        "dataset_name": DATA_FILE.name,
        "record_count": int(cleaned["Order ID"].nunique()),
        "products": sorted(cleaned["Product"].unique().tolist()),
        "regions": sorted(cleaned["Region"].unique().tolist()),
        "cities": sorted(cleaned["City"].unique().tolist()),
    })


@app.route("/api/kpis")
def api_kpis():
    cleaned, df = filtered_df()
    total_sales = float(df["Sales"].sum())
    total_orders = int(df["Order ID"].nunique())
    total_quantity = int(df["Quantity Ordered"].sum())
    total_profit = float(df["Profit"].sum())
    return jsonify({
        "total_sales": total_sales,
        "average_sales": total_sales / total_orders if total_orders else 0,
        "total_profit": total_profit,
        "profit_margin": (total_profit / total_sales * 100) if total_sales else 0,
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "filtered_count": len(df),
        "total_count": len(cleaned),
        "missing_total": sum(missing_summary(load_data()).values()),
    })


@app.route("/api/trend")
def api_trend():
    _, df = filtered_df()
    granularity = request.args.get("granularity", "day")
    return jsonify(compute_trend(df, granularity))


@app.route("/api/sales-analysis")
def api_sales_analysis():
    _, df = filtered_df()
    if df.empty:
        empty = {"labels": [], "values": []}
        return jsonify({"product_sales": empty, "region_sales": empty, "hourly_sales": empty,
                         "histogram": empty, "top_products": empty})
    product_sales = df.groupby("Product")["Sales"].sum()
    region_sales = df.groupby("Region")["Sales"].sum()
    hourly_sales = df.groupby("Hour")["Sales"].sum().reindex(range(24), fill_value=0)
    return jsonify({
        "product_sales": series_payload(product_sales),
        "region_sales": series_payload(region_sales),
        "hourly_sales": {"labels": [f"{h}:00" for h in hourly_sales.index], "values": [round(float(v), 2) for v in hourly_sales.values]},
        "histogram": compute_histogram(df),
        "top_products": series_payload(product_sales, limit=10),
    })


@app.route("/api/profit")
def api_profit():
    _, df = filtered_df()
    if df.empty:
        empty = {"labels": [], "values": []}
        return jsonify({"total_profit": 0, "margin": 0, "profit_by_region": empty,
                         "profit_by_product": empty, "top_profit_products": empty})
    total_profit = float(df["Profit"].sum())
    total_sales = float(df["Sales"].sum())
    profit_by_region = df.groupby("Region")["Profit"].sum()
    profit_by_product = df.groupby("Product")["Profit"].sum()
    return jsonify({
        "total_profit": total_profit,
        "margin": (total_profit / total_sales * 100) if total_sales else 0,
        "profit_by_region": series_payload(profit_by_region),
        "profit_by_product": series_payload(profit_by_product, limit=10),
        "top_profit_products": series_payload(profit_by_product, limit=10),
    })


@app.route("/api/forecast")
def api_forecast():
    _, df = filtered_df()
    periods = int(request.args.get("periods", 3))
    return jsonify(linear_forecast(df, periods))


@app.route("/api/insights")
def api_insights():
    _, df = filtered_df()
    return jsonify({"insights": generate_insights(df)})


@app.route("/api/table")
def api_table():
    _, df = filtered_df()
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(int(request.args.get("page_size", 20)), 100)
    total = len(df)
    start = (page - 1) * page_size
    page_df = df.iloc[start:start + page_size]
    rows = []
    for _, row in page_df.iterrows():
        rows.append({
            "order_id": row["Order ID"],
            "product": row["Product"],
            "quantity": int(row["Quantity Ordered"]),
            "price": float(row["Price Each"]),
            "sales": float(row["Sales"]),
            "profit": float(row["Profit"]),
            "date": row["Order Date"].strftime("%Y-%m-%d %H:%M"),
            "city": row["City"],
            "region": row["Region"],
        })
    return jsonify({"rows": rows, "total": total, "page": page, "page_size": page_size})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "Please select a CSV file."}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Only CSV files are supported."}), 400
    try:
        uploaded = pd.read_csv(file)
        missing_columns = [c for c in REQUIRED_COLUMNS if c not in uploaded.columns]
        if missing_columns:
            return jsonify({"success": False, "message": "Missing required columns: " + ", ".join(missing_columns)}), 400
        uploaded[REQUIRED_COLUMNS].to_csv(DATA_FILE, index=False)
        return jsonify({"success": True, "message": f"Dataset uploaded: {len(uploaded)} rows.", "record_count": len(uploaded)})
    except Exception as exc:
        return jsonify({"success": False, "message": f"Could not process the file: {exc}"}), 400


@app.route("/api/reset", methods=["POST"])
def api_reset():
    import subprocess, sys
    subprocess.run([sys.executable, str(BASE_DIR / "generate_dataset.py")], cwd=str(BASE_DIR), check=False)
    return jsonify({"success": True, "message": "Sample dataset restored."})


@app.route("/api/export")
def api_export():
    _, df = filtered_df()
    output = UPLOAD_FOLDER / "export_sales_data.csv"
    export_cols = ["Order ID", "Product", "Quantity Ordered", "Price Each", "Sales",
                   "Profit", "Order Date", "City", "Region"]
    df[export_cols].to_csv(output, index=False)
    return send_file(output, as_attachment=True, download_name="sales_data_export.csv")


if __name__ == "__main__":
    app.run(debug=True)
