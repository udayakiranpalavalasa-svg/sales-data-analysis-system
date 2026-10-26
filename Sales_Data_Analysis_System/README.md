# Sales Data Analysis System

**Data Analysis Essentials Cornerstone Project — Dept. of Artificial Intelligence & Machine Learning**

A Flask + Pandas/NumPy backend paired with a single-page, Chart.js-driven
dashboard — modeled on the project's target frontend design (KPI cards,
live filters, sidebar modules, AI insights panel, dark mode).

## 1. Architecture

- **Backend (`app.py`)** — loads and cleans the CSV, derives `Sales`,
  `Month`, `Hour`, `City` and `Region`, and exposes everything as a small
  JSON API. All the actual data analysis (groupby/aggregation, linear
  forecast, insight generation) happens here in Pandas/NumPy.
- **Frontend (`templates/index.html` + `static/js/app.js`)** — a single
  HTML page with all sections (Dashboard, Data Upload, Sales Analysis,
  Profit Analysis, Forecast, Data Table, About Project). Sidebar clicks
  swap sections instantly (no page reloads); filters call the API and
  redraw the Chart.js charts live.

No build step, no Node — just `python app.py` and a browser. Chart.js and
Bootstrap Icons load from a CDN.

## 2. Dataset Structure

`Sales_Data.csv` (bundled sample, 2000 orders) with the raw columns:

| Column            | Description                                   |
|-------------------|------------------------------------------------|
| Order ID          | Unique order identifier                         |
| Product           | Product name                                    |
| Quantity Ordered  | Units ordered                                   |
| Price Each        | Price per unit ($)                              |
| Order Date        | Timestamp of the order (MM/DD/YY HH:MM)         |
| Purchase Address  | Full delivery address (street, city, state ZIP) |

Derived during cleaning:
- **Sales** = Quantity Ordered × Price Each
- **Month** / **Hour** = extracted from Order Date
- **City** = parsed from Purchase Address
- **Region** *(enhancement)* = US Census region (Northeast/Midwest/South/West), mapped from the state in the address — the raw export has no Region column
- **EstUnitCost** / **Profit** *(enhancement)* = an assumed cost-to-price ratio per product (documented in `app.py` and on the About page), since the raw dataset has no actual cost data

The bundled sample includes a few blank rows and duplicate orders so the
cleaning step has something to demonstrate. Regenerate it anytime with
`python generate_dataset.py`.

## 3. Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**.

## 4. Pages / Modules

| Sidebar item      | What it shows                                                       |
|-------------------|------------------------------------------------------------------------|
| Dashboard         | 5 KPI cards, filters, Sales Trend chart (Daily/Weekly/Monthly)          |
| Data Upload       | Drag-and-drop CSV upload, required-column reference, dataset reset      |
| Sales Analysis    | Sales by product/region/hour, sales-value histogram, top 10 products   |
| Profit Analysis   | Estimated profit KPIs, profit by region, most profitable products      |
| Forecast          | Actual vs. linear-trend-forecast monthly sales (next 3 months)         |
| Data Table        | Paginated, filterable order-level records                              |
| About Project     | Abstract, enhancement assumptions, team, tech stack                    |

Filters (search / region / product / date range) are shared across every
data page and update all charts on that page live via `fetch()` — no
reload. AI Insights (sidebar panel or topbar button) generates a
rule-based natural-language summary from the currently filtered data.

## 5. JSON API

| Route                | Description                                    |
|-----------------------|-------------------------------------------------|
| `GET /api/meta`        | Dataset name, record count, filter dropdown options |
| `GET /api/kpis`        | Headline KPI numbers                              |
| `GET /api/trend`       | Sales trend series (`?granularity=day\|week\|month`) |
| `GET /api/sales-analysis` | Product/region/hourly series + histogram + top 10 |
| `GET /api/profit`      | Profit KPIs and profit-by-region/product series     |
| `GET /api/forecast`    | Actual + forecast monthly series, trend direction    |
| `GET /api/insights`    | Rule-based AI insights (list of strings)             |
| `GET /api/table`       | Paginated order rows (`?page=&page_size=`)           |
| `POST /api/upload`     | Replace the dataset with an uploaded CSV             |
| `POST /api/reset`      | Restore the bundled sample dataset                   |
| `GET /api/export`      | Download the current (filtered) dataset as CSV       |

All `GET` endpoints (except `/api/meta`) accept the shared filter
query params: `search`, `region`, `product`, `date_from`, `date_to`.

## 6. Tech Stack
Python, Flask, Pandas, NumPy · Chart.js, Bootstrap Icons · vanilla JavaScript.

## 7. Team
- Shaik Ayyaz Ahmed (25B11AIA96)
- P. Madhavan (25B11AI873)
- P. Udayakiran (25B11AI880)
- D. Pardhu (25B11AID04)

Guided by Mrs. A. Sophia — Department of Artificial Intelligence & Machine Learning, Aditya University.

## 8. Possible Future Enhancements
- Wire `/api/insights` up to a real LLM (Gemini/OpenAI/Anthropic) instead
  of the rule-based generator — swap the body of `generate_insights()` in
  `app.py` for an API call and keep the same JSON shape.
- Replace the estimated cost ratios with a real cost column once one is
  available (removes the Profit Analysis assumption entirely).
- Add a proper time-series model (Prophet/ARIMA) in place of the linear
  forecast for the Forecast page.
