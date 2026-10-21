# Text-to-SQL Retail Analytics Copilot

An autonomous Text-to-SQL data analytics copilot built with **LangChain**, **SQLAlchemy**, and **SQLite**. Translates natural language merchandising and supply chain queries into validated SQL, executes them against retail sales databases, and synthesizes executive business insights.

---

## 🏛️ System Architecture

```
User Question: "What was the average daily orders for the Apparels category last month?"
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │          LangChain SQL Agent                 │
         │      (create_sql_agent: 'tool-calling')      │
         └──────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       [sql_db_list_tables]           [sql_db_schema]
       Discovers daily_sales,         Inspects column types &
       products tables                sample records
                │                               │
                └───────────────┬───────────────┘
                                ▼
       [Formulate Dialect SQL with Casing & Date Logic]
       SELECT AVG(orders) FROM daily_sales 
       WHERE LOWER(category) LIKE '%apparel%' 
         AND strftime('%Y-%m', date) = '2026-09';
                                │
                                ▼
                       [sql_db_query]
                       Executes on retail_analytics.db
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                   Synthesized Business Insight                 │
│ "In September 2026, the Apparel category averaged 155.6 orders │
│  per day with $10,114.00 in daily revenue supported by 5.4 FTE"│
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
Retail-SQL-Copilot/
├── requirements.txt      # langchain, langchain-community, langchain-openai, sqlalchemy, pandas
├── database_setup.py     # SQLite schema definition and realistic synthetic retail data generator
├── agent.py              # LangChain SQLDatabase connection & tool-calling agent factory
├── main.py               # Main CLI runner accepting natural language retail queries
└── README.md             # Documentation, schema, and usage guide
```

---

## 📊 Database Schema (`retail_analytics.db`)

### 1. `daily_sales` Table
Captures historical daily performance across product categories:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | Auto-increment primary key |
| `date` | TEXT | Transaction date in `YYYY-MM-DD` ISO format |
| `category` | TEXT | Merchandise category (`Apparel`, `Electronics`, `Footwear`, `Home & Kitchen`, `Groceries`) |
| `orders` | INTEGER | Daily order volume |
| `revenue` | FLOAT | Gross daily revenue ($ USD) |
| `fte_count` | FLOAT | Full-Time Equivalent staff on duty |

### 2. `products` Table
Master product dimension catalog:

| Column | Type | Description |
| :--- | :--- | :--- |
| `sku` | TEXT (PK) | Stock Keeping Unit identifier (e.g. `SKU-APP-001`) |
| `category` | TEXT | Merchandise category |
| `price` | FLOAT | Retail unit price ($ USD) |
| `vendor` | TEXT | Supplier / vendor name |

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database & Generate Retail Data
```bash
python database_setup.py
```
This creates `retail_analytics.db` populated with:
- 21 catalog SKUs across 5 merchandise categories.
- ~600 historical daily records spanning the past 120 days with weekend volume uplift and staffing variance.

### 3. Run Queries via Main Runner
Set your OpenAI API key in `.env`:
```bash
OPENAI_API_KEY=sk-...
```

Run the default benchmark question:
```bash
python main.py
```
> **Default Query**: *"What was the average daily orders for the Apparels category last month?"*

Or pass any custom natural language analytics query:
```bash
python main.py "Which 3 product categories generated the highest total revenue over the last 30 days?"
```

```bash
python main.py "What is the average price of products supplied by UrbanThread Outfitters?"
```
