"""Main entry point for the Text-to-SQL Retail Analytics Copilot.
Accepts natural language analytics questions, invokes the LangChain SQL agent,
and prints the synthesized response.
"""

from datetime import date
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Ensure robust standard output encoding across platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent import DEFAULT_DB_PATH, create_retail_sql_agent
from database_setup import create_retail_database

load_dotenv()


def run_direct_sql_reference(db_path: Path, category: str = "Apparel"):
    """Reference query executed directly via sqlite3 to compute ground-truth metrics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Determine last month (YYYY-MM) relative to today
    today = date.today()
    year = today.year if today.month > 1 else today.year - 1
    month = today.month - 1 if today.month > 1 else 12
    last_month_str = f"{year:04d}-{month:02d}"

    sql = f"""
    SELECT 
        COUNT(*) as days_count,
        ROUND(AVG(orders), 2) as avg_orders,
        ROUND(AVG(revenue), 2) as avg_revenue,
        ROUND(AVG(fte_count), 2) as avg_fte
    FROM daily_sales 
    WHERE LOWER(category) LIKE LOWER('%{category}%')
      AND strftime('%Y-%m', date) = '{last_month_str}';
    """
    cursor.execute(sql)
    row = cursor.fetchone()
    conn.close()

    return {
        "month": last_month_str,
        "days_recorded": row[0],
        "avg_daily_orders": row[1],
        "avg_daily_revenue": row[2],
        "avg_daily_fte": row[3],
        "sql": sql.strip(),
    }


def query_copilot(user_query: str, db_path: Optional[str] = None):
    """Execute natural language query through the LangChain SQL agent."""
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # Initialize database if missing
    if not Path(db_path).exists():
        print("[Setup] Database not found. Generating synthetic retail dataset...")
        create_retail_database(db_path)

    print("\n" + "=" * 70)
    print("RETAIL ANALYTICS TEXT-TO-SQL COPILOT")
    print("=" * 70)
    print(f"User Query : '{user_query}'")
    print(f"Database   : {Path(db_path).name}")
    print("-" * 70)

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("\n[NOTICE] 'OPENAI_API_KEY' is not configured.")
        print("To run with an active LLM, set your key in a .env file:")
        print("    OPENAI_API_KEY=sk-...\n")

        # Execute direct ground-truth query as reference verification
        print("Computing direct SQL ground-truth reference for verification:")
        ref = run_direct_sql_reference(Path(db_path), category="Apparel")
        print(f"\nExecuted SQL:\n{ref['sql']}\n")
        print(f"Ground Truth Result for {ref['month']} ({ref['days_recorded']} days):")
        print(f"  * Average Daily Orders  : {ref['avg_daily_orders']}")
        print(f"  * Average Daily Revenue : ${ref['avg_daily_revenue']:,.2f}")
        print(f"  * Average Daily FTE     : {ref['avg_daily_fte']} staff")
        print("\n" + "=" * 70)
        return

    # Execute with LangChain Agent
    try:
        agent_executor, _ = create_retail_sql_agent(db_path=db_path, verbose=True)
        response = agent_executor.invoke({"input": user_query})

        print("\n" + "=" * 70)
        print("SYNTHESIZED COPILOT RESPONSE:")
        print("=" * 70)
        print(response.get("output", ""))
        print("=" * 70)

    except Exception as e:
        print(f"\n[Agent Error] Could not complete agent execution: {e}")


def main():
    default_query = "What was the average daily orders for the Apparels category last month?"
    query = sys.argv[1] if len(sys.argv) > 1 else default_query
    query_copilot(query)


if __name__ == "__main__":
    main()
