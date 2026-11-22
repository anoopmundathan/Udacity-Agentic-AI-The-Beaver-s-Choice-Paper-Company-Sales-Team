# Munder Difflin Agent Workflow (4 agents, smolagents)

```mermaid
flowchart TD
    C[/Customer request + request date/] --> O
    O["ORCHESTRATOR<br/>Parses items, quantities, deadline.<br/>Delegates, composes the final customer reply<br/>(no internal costs/errors)"]
    O -->|"items + date"| I
    O -->|"items + date"| Q
    O -->|"items + date + deadline (orders only)"| R
    I -->|"stock status / reorder result"| O
    Q -->|"quote lines, total, discount rationale"| O
    R -->|"fulfilled or rejected + reasons"| O
    O --> A[/Final reply: quote, delivery date, rationale or rejection reason/]

    I["INVENTORY AGENT<br/>Owns stock levels and supplier restocking"]
    Q["QUOTING AGENT<br/>Owns pricing and bulk discounts"]
    R["ORDERING AGENT<br/>Owns sales finalisation and order feasibility"]

    I --- I1["check_all_inventory<br/>Snapshot of stock + items below minimum<br/>uses get_all_inventory"]
    I --- I2["check_item_stock<br/>Stock of one item on a date<br/>uses get_stock_level"]
    I --- I3["estimate_supplier_delivery<br/>Lead time for a restock size<br/>uses get_supplier_delivery_date"]
    I --- I4["reorder_stock<br/>Buy stock if cash allows<br/>uses get_cash_balance, get_supplier_delivery_date, create_transaction(stock_orders)"]
    I --- I5["find_catalog_items<br/>Map customer wording to catalog names"]

    Q --- Q1["get_quote_history<br/>Past similar quotes to guide price<br/>uses search_quote_history"]
    Q --- Q2["generate_quote<br/>Price lines with bulk discount, show stock/delivery<br/>uses get_stock_level, get_supplier_delivery_date"]

    R --- R1["check_financial_health<br/>Cash, inventory value, top sellers before big orders<br/>uses generate_financial_report, get_cash_balance"]
    R --- R2["fulfill_order<br/>Restock if needed, record sale per line, skip impossible lines with a reason<br/>uses get_stock_level, get_supplier_delivery_date, get_cash_balance, create_transaction(sales)"]

    I1 & I2 & I4 & Q2 & R1 & R2 <--> DB[("SQLite: transactions, inventory, quotes, quote_requests")]
    Q1 --> DB
```

Responsibility boundaries: the inventory agent is the only one that answers stock questions and reorders proactively;
the quoting agent never writes to the database; the ordering agent is the only one that records sales
(it restocks only as a side effect of a confirmed order). `find_catalog_items` is a read-only lookup shared by the workers.

`init_database` and `generate_sample_inventory` are used by the test harness to build the database and starting stock.
