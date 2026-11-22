import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


import json
import re
import difflib
from smolagents import ToolCallingAgent, OpenAIServerModel, tool

dotenv.load_dotenv()

# Model served through the Udacity/Vocareum OpenAI-compatible proxy
model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base="https://openai.vocareum.com/v1",
    api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
)

CATALOG = {p["item_name"]: p for p in paper_supplies}
RESTOCK_BUFFER = 1.2  # order 20% above the shortfall/min level to avoid repeated reorders


def _resolve_item(name: str) -> Union[str, None]:
    """Map a free-text item name to an exact catalog name (case-insensitive, fuzzy)."""
    if name in CATALOG:
        return name
    lowered = {k.lower(): k for k in CATALOG}
    if name.lower() in lowered:
        return lowered[name.lower()]
    match = difflib.get_close_matches(name.lower(), list(lowered), n=1, cutoff=0.85)
    return lowered[match[0]] if match else None


def _discount_rate(quantity: int) -> float:
    """Tiered bulk discount to encourage larger orders."""
    if quantity >= 5000:
        return 0.15
    if quantity >= 1000:
        return 0.10
    if quantity >= 500:
        return 0.07
    if quantity >= 100:
        return 0.03
    return 0.0


def _line_price(item_name: str, quantity: int) -> Dict:
    unit = CATALOG[item_name]["unit_price"]
    rate = _discount_rate(quantity)
    return {
        "item_name": item_name,
        "quantity": quantity,
        "unit_price": unit,
        "discount_pct": round(rate * 100, 1),
        "line_total": round(unit * quantity * (1 - rate), 2),
    }


def _parse_items(items_json: str) -> List[Dict]:
    items = json.loads(items_json)
    if isinstance(items, dict):
        items = [items]
    return items


# Simulated "today", set from the request being processed. Tools use it instead of any
# date typed by an LLM, so malformed dates can never produce false "no stock / no cash" answers.
current_request_date = None


def _effective_date(llm_date: str) -> str:
    """Return the request date for the active request, else a normalised YYYY-MM-DD of llm_date."""
    if current_request_date:
        return current_request_date
    return str(llm_date)[:10]


"""Tools for the agents. They combine the database helpers above and apply business criteria."""


# Tools for inventory agent

@tool
def find_catalog_items(query: str) -> str:
    """Find items in the company catalog that match a free-text description.
    Use this to map customer wording (e.g. 'heavy cardstock') to exact catalog names.

    Args:
        query: Free-text item description from the customer.
    """
    by_lower = {n.lower(): n for n in CATALOG}
    q = query.lower()
    hits = [n for low, n in by_lower.items() if q in low or low in q]
    for m in difflib.get_close_matches(q, list(by_lower), n=5, cutoff=0.4):
        if by_lower[m] not in hits:
            hits.append(by_lower[m])
    if not hits:
        words = [w for w in q.replace("-", " ").split() if len(w) > 3]
        hits = [n for n in CATALOG if any(w in n.lower() for w in words)]
    if not hits:
        return "No matching catalog item; the item is not sold by Munder Difflin."
    return json.dumps([{"item_name": h, "unit_price": CATALOG[h]["unit_price"]} for h in hits[:8]])


@tool
def check_all_inventory(as_of_date: str) -> str:
    """List every item currently in stock with its quantity, plus items at/below minimum level.

    Args:
        as_of_date: ISO date (YYYY-MM-DD) of the snapshot.
    """
    stock = get_all_inventory(_effective_date(as_of_date))
    inv = pd.read_sql("SELECT item_name, min_stock_level FROM inventory", db_engine)
    mins = dict(zip(inv["item_name"], inv["min_stock_level"]))
    low = {k: {"stock": int(stock.get(k, 0)), "min": int(v)}
           for k, v in mins.items() if stock.get(k, 0) <= v}
    return json.dumps({"in_stock": {k: int(v) for k, v in stock.items()}, "at_or_below_minimum": low})


@tool
def check_item_stock(item_name: str, as_of_date: str) -> str:
    """Check the stock level of one item.

    Args:
        item_name: Item name (fuzzy matched to the catalog).
        as_of_date: ISO date (YYYY-MM-DD).
    """
    name = _resolve_item(item_name)
    if not name:
        return f"'{item_name}' is not in the catalog."
    stock = int(get_stock_level(name, _effective_date(as_of_date))["current_stock"].iloc[0])
    return json.dumps({"item_name": name, "current_stock": stock, "carried_in_inventory": _carried(name)})


def _carried(name: str) -> bool:
    inv = pd.read_sql("SELECT item_name FROM inventory", db_engine)
    return name in set(inv["item_name"])


def _restock(name: str, quantity: int, order_date: str) -> Dict:
    """Place a supplier order. Stock is booked on the supplier delivery date."""
    cost = round(CATALOG[name]["unit_price"] * quantity, 2)
    cash = get_cash_balance(order_date)
    if cost > cash:
        return {"ok": False, "reason": "restock_unavailable"}  # internal; never shown to customers
    delivery = get_supplier_delivery_date(order_date, quantity)
    tid = create_transaction(name, "stock_orders", quantity, cost, delivery)
    return {"ok": True, "transaction_id": tid, "item_name": name, "quantity": quantity,
            "cost": cost, "delivery_date": delivery}


@tool
def estimate_supplier_delivery(order_date: str, quantity: int) -> str:
    """Estimate when a supplier order of a given size would arrive.

    Args:
        order_date: ISO date (YYYY-MM-DD) the order would be placed.
        quantity: Number of units to order.
    """
    return get_supplier_delivery_date(_effective_date(order_date), int(quantity))


@tool
def reorder_stock(item_name: str, quantity: int, order_date: str) -> str:
    """Order more stock from the supplier (spends cash, stock arrives on the delivery date).
    Only reorder when stock is at/below minimum level or an order needs it.

    Args:
        item_name: Item name (fuzzy matched to the catalog).
        quantity: Units to order.
        order_date: ISO date (YYYY-MM-DD) the order is placed.
    """
    name = _resolve_item(item_name)
    if not name:
        return f"'{item_name}' is not in the catalog."
    return json.dumps(_restock(name, int(quantity), _effective_date(order_date)))


# Tools for quoting agent

@tool
def get_quote_history(search_terms: str) -> str:
    """Search past quotes to guide pricing.

    Args:
        search_terms: Comma-separated keywords, e.g. 'cardstock,event'.
    """
    terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    rows = search_quote_history(terms, limit=3)
    for r in rows:
        r["original_request"] = str(r["original_request"])[:300]
        r["quote_explanation"] = str(r["quote_explanation"])[:300]
    return json.dumps(rows, default=str)


@tool
def generate_quote(items_json: str, as_of_date: str) -> str:
    """Price an order with bulk discounts and check stock/lead time for each line.

    Args:
        items_json: JSON list like [{"item_name": "A4 paper", "quantity": 500}]. Use catalog names.
        as_of_date: ISO date (YYYY-MM-DD) of the request.
    """
    as_of_date = _effective_date(as_of_date)
    lines, unknown, total = [], [], 0.0
    for it in _parse_items(items_json):
        name = _resolve_item(it["item_name"])
        if not name:
            unknown.append(it["item_name"])
            continue
        qty = int(it["quantity"])
        line = _line_price(name, qty)
        stock = int(get_stock_level(name, as_of_date)["current_stock"].iloc[0])
        line["in_stock"] = stock
        line["earliest_delivery"] = as_of_date if stock >= qty else get_supplier_delivery_date(as_of_date, qty - stock)
        lines.append(line)
        total += line["line_total"]
    return json.dumps({"lines": lines, "total": round(total, 2), "not_sold": unknown})


# Tools for ordering agent

@tool
def check_financial_health(as_of_date: str) -> str:
    """Return cash balance, inventory value, total assets and top sellers (internal check before large orders).

    Args:
        as_of_date: ISO date (YYYY-MM-DD).
    """
    as_of_date = _effective_date(as_of_date)
    rep = generate_financial_report(as_of_date)
    rep.pop("inventory_summary")
    rep["cash_balance"] = round(get_cash_balance(as_of_date), 2)
    return json.dumps(rep, default=str)


@tool
def fulfill_order(items_json: str, request_date: str, deadline: str = "") -> str:
    """Fulfil a customer order: for each line, restock from the supplier if needed, then record the sale.
    Lines that are impossible (unknown item, supplier cannot deliver by the deadline, restock not
    possible) are skipped with a customer-safe reason; feasible lines are still fulfilled.

    Args:
        items_json: JSON list like [{"item_name": "A4 paper", "quantity": 500}]. Use catalog names.
        request_date: ISO date (YYYY-MM-DD) the customer asked.
        deadline: Optional ISO date (YYYY-MM-DD) by which the customer needs delivery; empty if none.
    """
    request_date = _effective_date(request_date)
    deadline = str(deadline)[:10] if deadline else ""
    done, rejected, revenue = [], [], 0.0
    for it in _parse_items(items_json):
        name = _resolve_item(it["item_name"])
        if not name:
            rejected.append({"item_name": it["item_name"], "reason": "This product is not part of our catalog."})
            continue
        qty = int(it["quantity"])
        stock = int(get_stock_level(name, request_date)["current_stock"].iloc[0])
        ready, restock_qty = request_date, 0
        if stock < qty:
            # order the shortfall plus a buffer so the next order does not trigger another reorder
            restock_qty = int((qty - stock) * RESTOCK_BUFFER) + 1
            ready = get_supplier_delivery_date(request_date, restock_qty)
        if deadline and ready > deadline:
            rejected.append({"item_name": name, "reason":
                             f"Earliest possible delivery is {ready}, after your required date {deadline}."})
            continue
        if restock_qty and not _restock(name, restock_qty, request_date)["ok"]:
            rejected.append({"item_name": name, "reason":
                             "We cannot supply the requested quantity right now."})
            continue
        line = _line_price(name, qty)
        create_transaction(name, "sales", qty, line["line_total"], ready)
        revenue += line["line_total"]
        done.append({**line, "delivery_date": ready})
    return json.dumps({"fulfilled_lines": done, "unfulfilled_lines": rejected,
                       "total_charged": round(revenue, 2)})


# Set up your agents and create an orchestration agent that will manage them.

inventory_agent = ToolCallingAgent(
    tools=[find_catalog_items, check_all_inventory, check_item_stock, estimate_supplier_delivery, reorder_stock],
    model=model,
    name="inventory_agent",
    description="Answers stock-level questions, maps customer item wording to catalog names, "
                "estimates supplier lead times and reorders stock when items are low.",
    max_steps=8,
)

quoting_agent = ToolCallingAgent(
    tools=[find_catalog_items, get_quote_history, generate_quote],
    model=model,
    name="quoting_agent",
    description="Builds customer quotes with bulk discounts. Give it the request date and the "
                "items/quantities; it returns line items, total and earliest delivery.",
    max_steps=8,
)

ordering_agent = ToolCallingAgent(
    tools=[find_catalog_items, check_financial_health, fulfill_order],
    model=model,
    name="ordering_agent",
    description="Finalises sales: restocks if needed, records transactions, and skips lines that are "
                "impossible (unknown item, missed deadline, cannot restock) with a reason. "
                "Give it the request date, items/quantities and any customer deadline.",
    max_steps=8,
)

orchestrator = ToolCallingAgent(
    tools=[],
    model=model,
    managed_agents=[inventory_agent, quoting_agent, ordering_agent],
    name="orchestrator",
    instructions=(
        "You are the customer-facing orchestrator for Munder Difflin Paper Company. For each request: "
        "1) extract items (use the exact wording, quantities in units/sheets; 1 ream=500 sheets, 1 box=5000 sheets "
        "unless stated) and any delivery deadline converted to YYYY-MM-DD relative to the request date; "
        "2) ask inventory_agent for stock status (and to reorder low-stock items); "
        "3) ask quoting_agent for the quote; "
        "4) treat every request as an ORDER and ALWAYS call ordering_agent with the request date, items and "
        "deadline, unless the customer explicitly only asks for a price/quote. "
        "Lines the ordering agent reports as unfulfilled are rejected with its reason; fulfilled lines are final. "
        "Quote the total using the ordering agent's total_charged for fulfilled lines. "
        "The final reply must: list each item with quantity, price and delivery date, explain any bulk discount, "
        "and give a clear reason for each item that cannot be supplied (not in catalog, cannot arrive by the "
        "required date, or currently cannot be supplied) with an alternative if one exists. "
        "NEVER mention cash, funds, budget, costs, margins, restocking finances, system errors or 'out of stock "
        "because of money' to the customer; say 'we cannot supply this quantity right now' instead. "
        "Always pass the request date to sub-agents."
    ),
    max_steps=12,
)


def call_your_multi_agent_system(request_with_date: str) -> str:
    """Run one customer request through the orchestrator and return the customer-facing reply."""
    global current_request_date
    match = re.search(r"Date of request: (\d{4}-\d{2}-\d{2})", request_with_date)
    current_request_date = match.group(1) if match else None
    try:
        return str(orchestrator.run(request_with_date, reset=True))
    except Exception as e:
        print(f"Internal error: {e}")  # logged internally, never shown to the customer
        return "Sorry, we could not process your request right now. Please try again or contact our sales team."


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        response = call_your_multi_agent_system(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
