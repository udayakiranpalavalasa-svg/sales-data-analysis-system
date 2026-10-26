"""
Generates a realistic sample e-commerce sales dataset (Sales_Data.csv)
matching the schema used in the reference Colab analysis script:

  Order ID, Product, Quantity Ordered, Price Each, Order Date, Purchase Address

Run:  python generate_dataset.py
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(7)

PRODUCTS = {
    "USB-C Charging Cable": 11.95,
    "Lightning Charging Cable": 14.95,
    "AAA Batteries (4-pack)": 2.99,
    "AA Batteries (4-pack)": 3.84,
    "Wired Headphones": 11.99,
    "Apple Airpods Headphones": 150.00,
    "Bose SoundSport Headphones": 99.99,
    "20in Monitor": 109.99,
    "27in FHD Monitor": 149.99,
    "27in 4K Gaming Monitor": 389.99,
    "34in Ultrawide Monitor": 379.99,
    "Flatscreen TV": 300.00,
    "iPhone": 700.00,
    "Google Phone": 600.00,
    "Vareebadd Phone": 400.00,
    "LG Washing Machine": 600.00,
    "LG Dryer": 600.00,
    "Macbook Pro Laptop": 1700.00,
    "ThinkPad Laptop": 999.99,
}
PRODUCT_NAMES = list(PRODUCTS.keys())

CITIES = [
    ("San Francisco", "CA"), ("Los Angeles", "CA"), ("New York City", "NY"),
    ("Boston", "MA"), ("Dallas", "TX"), ("Austin", "TX"),
    ("Seattle", "WA"), ("Atlanta", "GA"), ("Portland", "OR"), ("Portland", "ME"),
]

STREET_NAMES = ["Main St", "Elm St", "Cedar St", "Willow St", "Highland St", "Maple St", "Oak St", "Church St"]

N_ORDERS = 2000
YEAR = 2019
order_id_start = 141234

rows = []
oid = order_id_start
for i in range(N_ORDERS):
    month = np.random.choice(range(1, 13), p=[
        0.055, 0.05, 0.06, 0.065, 0.075, 0.08,
        0.085, 0.08, 0.075, 0.09, 0.105, 0.18   # Dec spike (holiday shopping)
    ])
    day = int(np.random.randint(1, 28))
    hour_weights = np.array([
        0.005, 0.003, 0.002, 0.002, 0.003, 0.006, 0.012, 0.025,
        0.04, 0.05, 0.06, 0.065, 0.07, 0.065, 0.06, 0.06,
        0.065, 0.07, 0.075, 0.07, 0.06, 0.04, 0.02, 0.01,
    ])
    hour = int(np.random.choice(range(24), p=hour_weights / hour_weights.sum()))
    minute = int(np.random.randint(0, 60))
    order_date = datetime(YEAR, month, day, hour, minute)

    product = np.random.choice(PRODUCT_NAMES)
    price = PRODUCTS[product]
    # cheaper items bought in bigger multiples
    if price < 20:
        qty = int(np.random.choice([1, 2, 3, 4, 5], p=[0.5, 0.25, 0.13, 0.07, 0.05]))
    else:
        qty = int(np.random.choice([1, 2, 3], p=[0.82, 0.13, 0.05]))

    city, state = CITIES[np.random.randint(0, len(CITIES))]
    street_num = np.random.randint(1, 999)
    street = np.random.choice(STREET_NAMES)
    zip_code = np.random.randint(10000, 99999)
    address = f"{street_num} {street}, {city}, {state} {zip_code}"

    oid += 1
    rows.append({
        "Order ID": oid,
        "Product": product,
        "Quantity Ordered": qty,
        "Price Each": price,
        "Order Date": order_date.strftime("%m/%d/%y %H:%M"),
        "Purchase Address": address,
    })

df = pd.DataFrame(rows)

# Inject a handful of realistic data-quality issues (as in real Kaggle exports)
# so the cleaning step in the reference script has something to remove.
blank_rows = pd.DataFrame([{c: np.nan for c in df.columns}] * 8)
dup_rows = df.sample(6, random_state=1)
df = pd.concat([df, blank_rows, dup_rows], ignore_index=True)
df = df.sample(frac=1, random_state=2).reset_index(drop=True)  # shuffle like raw export

df.to_csv("Sales_Data.csv", index=False)
print(f"Generated Sales_Data.csv with {len(df)} rows (including blank rows & duplicates).")
