"""LangChain Text-to-SQL Agent for Retail Analytics.
Initializes the SQLDatabase connection, ChatOpenAI with 'tool-calling' agent type,
and equips the agent with a senior retail data analyst system prompt.
"""

from datetime import date
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "retail_analytics.db"


def get_retail_analyst_system_prompt() -> str:
    """Build domain-specific system instructions for retail analytics."""
    today_str = date.today().strftime("%Y-%m-%d")

    return f"""You are an expert Senior Retail Data Analyst Copilot.
Your job is to assist category managers, merchandising directors, and supply chain executives
by querying the retail relational database and synthesizing clear business insights.

The current system date is: {today_str}.

Operational Guidelines:
1. SCHEMA FIRST: Always inspect the database tables and columns before writing SQL.
2. TABLES:
   - `daily_sales`: date (TEXT, YYYY-MM-DD), category (TEXT), orders (INT), revenue (FLOAT), fte_count (FLOAT).
   - `products`: sku (TEXT), category (TEXT), price (FLOAT), vendor (TEXT).
3. CATEGORY MATCHING:
   - Retail terms may differ in singular vs plural in user prompts (e.g., 'Apparels' vs 'Apparel', 'Footwears' vs 'Footwear').
   - Use flexible matching such as `LOWER(category) LIKE '%apparel%'` to avoid empty results.
4. DATE HANDLING:
   - Dates are stored as ISO 'YYYY-MM-DD'.
   - For relative dates (e.g., 'last month', 'last 30 days', 'last quarter'), use SQLite date functions such as `strftime('%Y-%m', date)` or `date(date, ...)`.
   - 'Last month' means the immediately preceding full calendar month relative to {today_str}.
5. READ-ONLY: Only execute SELECT statements. Never execute INSERT, UPDATE, DELETE, or DROP.
6. SYNTHESIZED RESPONSE:
   - State the primary numerical answer clearly up-front (e.g., Average Daily Orders).
   - Round floats to 2 decimal places.
   - Conclude with a 1-sentence analytical or operational takeaway.
"""


def create_retail_sql_agent(
    db_path: Optional[str] = None,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    verbose: bool = True,
):
    """Instantiate and return a LangChain SQL Agent with tool-calling capabilities."""
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # Ensure database exists
    if not Path(db_path).exists():
        from database_setup import create_retail_database
        print(f"[Agent Setup] Database not found. Initializing new database at {db_path}...")
        create_retail_database(db_path)

    # 1. Connect to SQLite via LangChain SQLDatabase
    db_uri = f"sqlite:///{Path(db_path).resolve()}"
    db = SQLDatabase.from_uri(
        db_uri,
        sample_rows_in_table_info=3,
        include_tables=["daily_sales", "products"],
    )

    # 2. Check API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n[WARNING] 'OPENAI_API_KEY' is not set in environment or .env file.")
        print("Please set OPENAI_API_KEY to run live queries with OpenAI models.\n")

    # 3. Initialize Chat Model
    llm = ChatOpenAI(
        model="openai/gpt-oss-120b",
        temperature=temperature,
        api_key=api_key or "placeholder-key-for-initialization",
        base_url="https://api.groq.com/openai/v1"
    )

    # 4. Create SQL Agent with tool-calling agent type
    system_prompt = get_retail_analyst_system_prompt()
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",
        verbose=verbose,
        prefix=system_prompt,
        max_iterations=10,
    )

    return agent_executor, db
