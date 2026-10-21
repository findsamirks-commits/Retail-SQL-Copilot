"""Database initialization script for Retail Analytics Copilot.
Uses SQLite and SQLAlchemy to define schema and generate realistic synthetic
data across daily_sales and products tables.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
import random
from typing import Optional

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    String,
    create_engine,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class DailySale(Base):
    """Daily sales performance metrics grouped by retail category."""

    __tablename__ = "daily_sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)  # Format: YYYY-MM-DD
    category = Column(String(50), nullable=False, index=True)
    orders = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)
    fte_count = Column(Float, nullable=False)  # Full-Time Equivalent staff


class Product(Base):
    """Catalog product dimensions and pricing."""

    __tablename__ = "products"

    sku = Column(String(50), primary_key=True)
    category = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    vendor = Column(String(100), nullable=False)


# --- Seed Catalog Dimensions ---
CATALOG_ITEMS = [
    # Apparel
    {"sku": "SKU-APP-001", "category": "Apparel", "price": 45.00, "vendor": "UrbanThread Outfitters"},
    {"sku": "SKU-APP-002", "category": "Apparel", "price": 89.99, "vendor": "UrbanThread Outfitters"},
    {"sku": "SKU-APP-003", "category": "Apparel", "price": 120.00, "vendor": "SummitWear Co."},
    {"sku": "SKU-APP-004", "category": "Apparel", "price": 32.50, "vendor": "CottonCraft Mills"},
    {"sku": "SKU-APP-005", "category": "Apparel", "price": 64.00, "vendor": "SummitWear Co."},
    # Electronics
    {"sku": "SKU-ELE-001", "category": "Electronics", "price": 149.99, "vendor": "AcousticTech Global"},
    {"sku": "SKU-ELE-002", "category": "Electronics", "price": 299.00, "vendor": "AcousticTech Global"},
    {"sku": "SKU-ELE-003", "category": "Electronics", "price": 49.50, "vendor": "VoltStream Innovations"},
    {"sku": "SKU-ELE-004", "category": "Electronics", "price": 89.00, "vendor": "VoltStream Innovations"},
    {"sku": "SKU-ELE-005", "category": "Electronics", "price": 180.00, "vendor": "NexusHub Electronics"},
    # Footwear
    {"sku": "SKU-FTW-001", "category": "Footwear", "price": 110.00, "vendor": "StrideFlex Athletics"},
    {"sku": "SKU-FTW-002", "category": "Footwear", "price": 145.00, "vendor": "StrideFlex Athletics"},
    {"sku": "SKU-FTW-003", "category": "Footwear", "price": 85.00, "vendor": "ApexTrail Boots"},
    {"sku": "SKU-FTW-004", "category": "Footwear", "price": 60.00, "vendor": "CasualWalkers Inc."},
    # Home & Kitchen
    {"sku": "SKU-HNK-001", "category": "Home & Kitchen", "price": 75.00, "vendor": "CulinaryCraftware"},
    {"sku": "SKU-HNK-002", "category": "Home & Kitchen", "price": 130.00, "vendor": "CulinaryCraftware"},
    {"sku": "SKU-HNK-003", "category": "Home & Kitchen", "price": 35.00, "vendor": "HomeHarmony Goods"},
    {"sku": "SKU-HNK-004", "category": "Home & Kitchen", "price": 49.99, "vendor": "HomeHarmony Goods"},
    # Groceries
    {"sku": "SKU-GRO-001", "category": "Groceries", "price": 12.50, "vendor": "OrganicFields Cooperative"},
    {"sku": "SKU-GRO-002", "category": "Groceries", "price": 18.00, "vendor": "OrganicFields Cooperative"},
    {"sku": "SKU-GRO-003", "category": "Groceries", "price": 8.75, "vendor": "FreshFarm Distributors"},
]

CATEGORY_PROFILES = {
    "Apparel": {"base_orders": 140, "order_jitter": 40, "aov": 65.0, "base_fte": 5.0},
    "Electronics": {"base_orders": 85, "order_jitter": 25, "aov": 185.0, "base_fte": 4.5},
    "Footwear": {"base_orders": 95, "order_jitter": 30, "aov": 105.0, "base_fte": 4.0},
    "Home & Kitchen": {"base_orders": 110, "order_jitter": 35, "aov": 72.0, "base_fte": 4.5},
    "Groceries": {"base_orders": 310, "order_jitter": 75, "aov": 38.0, "base_fte": 8.0},
}


def create_retail_database(
    db_path: str = "retail_analytics.db",
    days_back: int = 120,
    seed: int = 42,
) -> str:
    """Initialize SQLite database and populate with synthetic retail metrics."""
    random.seed(seed)
    db_file = Path(db_path).resolve()
    db_uri = f"sqlite:///{db_file}"

    engine = create_engine(db_uri, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Insert Products
    for item in CATALOG_ITEMS:
        prod = Product(
            sku=item["sku"],
            category=item["category"],
            price=item["price"],
            vendor=item["vendor"],
        )
        session.add(prod)

    # 2. Insert Daily Sales over the historical window
    # End date anchor (e.g. today or late October 2026)
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    daily_sales_records = []
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday()
        # Weekend demand uplift multiplier (Friday/Saturday/Sunday)
        weekend_mult = 1.25 if day_of_week in (4, 5, 6) else 1.0

        for cat, prof in CATEGORY_PROFILES.items():
            order_var = random.randint(-prof["order_jitter"], prof["order_jitter"])
            orders = max(10, int((prof["base_orders"] + order_var) * weekend_mult))

            # Revenue with slight basket price variance
            aov_var = random.uniform(-0.10, 0.12)
            unit_aov = prof["aov"] * (1.0 + aov_var)
            revenue = round(orders * unit_aov, 2)

            # Labor staffing aligned with order volume
            fte_var = random.uniform(-0.5, 0.8)
            fte_count = round(max(2.0, prof["base_fte"] * weekend_mult + fte_var), 1)

            sale = DailySale(
                date=date_str,
                category=cat,
                orders=orders,
                revenue=revenue,
                fte_count=fte_count,
            )
            daily_sales_records.append(sale)

        current_date += timedelta(days=1)

    session.bulk_save_objects(daily_sales_records)
    session.commit()

    # Verify counts
    total_sales_rows = session.query(DailySale).count()
    total_products = session.query(Product).count()
    session.close()

    print(f"[Database Setup] SQLite database ready at: {db_file}")
    print(f"  • 'products' table populated with {total_products} SKUs")
    print(f"  • 'daily_sales' table populated with {total_sales_rows} records ({start_date} to {end_date})")

    return db_uri


if __name__ == "__main__":
    create_retail_database()
