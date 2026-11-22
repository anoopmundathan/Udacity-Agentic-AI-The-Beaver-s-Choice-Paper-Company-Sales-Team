# Munder Difflin Multi-Agent System – Report

## System explanation
Built with **smolagents** (`ToolCallingAgent`, `gpt-4o-mini` via the Vocareum proxy). Four agents (limit is five); see `agent_workflow.md` for the diagram.

| Agent | Role | Tools (starter helper used) |
|---|---|---|
| Orchestrator | Parses the request, extracts items/deadline, delegates, writes the customer reply (hides internal cash/margins) | managed agents only |
| Inventory | Stock questions, catalog mapping, supplier lead times, reorders | `check_all_inventory` (`get_all_inventory`), `check_item_stock` (`get_stock_level`), `estimate_supplier_delivery` (`get_supplier_delivery_date`), `reorder_stock` (`get_cash_balance`, `create_transaction`) |
| Quoting | Quotes with bulk discounts (3% ≥100, 7% ≥500, 10% ≥1000, 15% ≥5000 units) | `get_quote_history` (`search_quote_history`), `generate_quote` |
| Ordering | Finalises sales | `check_financial_health` (`generate_financial_report`, `get_cash_balance`), `fulfill_order` (`create_transaction`) |

Why this architecture: the three recommended business functions (stock, pricing, sales) each have different data needs and failure modes, so each gets one worker with a narrow toolset; this keeps prompts short and tool choice reliable. A single orchestrator is the only agent that talks to the customer, which keeps replies consistent and prevents internal details from leaking. Four agents leave headroom under the five-agent limit. Decisions that must be exact (prices, stock, cash, dates) are made by deterministic tools; the LLM handles language understanding and explanation.

Key design choices:
- Pricing and fulfilment logic live in deterministic tools, not in the LLM, so numbers are consistent between quote and sale.
- `fulfill_order` handles each line independently: it restocks if needed, records the sale, and skips impossible lines (unknown item, deadline shorter than supplier lead time, restock not possible) with a customer-safe reason, so partial orders are still fulfilled.
- Tools always use the date of the active request (set by `call_your_multi_agent_system`) rather than a date typed by an LLM, which avoids false "no stock / no cash" results.
- Restocks are booked on the supplier delivery date, so stock is only usable after it arrives; sales are dated at availability.
- Fuzzy catalog matching (`find_catalog_items`) maps customer wording to exact items; unmatched items are refused.

## Evaluation
The system was run on all 20 requests in `quote_requests_sample.csv` (output in `test_results.csv`).

**Cash and fulfilment.** Cash changed on requests 5 (+$90.15, sale), 7 (−$140.00, restock), 12 (+$126.10, sale), 14 (−$240.00, restock) and 15 (−$23.60, restock), so the "at least three cash changes" criterion is met. Request 5 was clearly fulfilled in full (500 colored paper + 300 cardstock, $90.15) and request 12 was fulfilled in part (cardstock sale recorded). Most other requests were answered with a quote and an explanation of why they could not be completed.

**Strengths**
- Rejections come with specific reasons: items not in the catalog (balloons, tickets, posters, table napkins), delivery deadlines shorter than supplier lead time (requests 15, 17, 19), and stock shortfalls. This satisfies the requirement that not every request is fulfilled.
- Bulk discounts are applied and mentioned (e.g. 7% on 500 sheets, 10% on 2,000 sheets in requests 16 and 19), and replies offer alternatives (e.g. other cardstock or poster paper options in requests 1, 14 and 18).
- Restocking is triggered by real orders (requests 5, 7, 14), with the stock booked on the supplier delivery date, so the cash balance and inventory value move consistently.
- Impossible constraints were recognised rather than silently accepted: the replies state when an item cannot arrive by the requested date.

**Weaknesses found**
- Only about two requests resulted in recorded sales, below the target of three fulfilled orders. Several requests that should have been fulfilled from stock were only quoted, because the orchestrator did not always call the ordering agent.
- Several replies claim items are "out of stock" and cash is "$0.00" (requests 3, 4, 6, 8, 9, 13, 17), although the database held stock and about $45,000 in cash. This points to sub-agents passing a wrong or empty `as_of_date` to the tools. Date comparisons are string-based, so the seed date `2025-01-01T00:00:00` sorts after a plain `2025-01-01`, which would produce zero stock and zero cash.
- Customer replies disclose internal information ("insufficient cash", "cash reserves", "$0.00"), which violates the customer-facing requirement.
- Some wording is inconsistent: request 2 says items were "reordered" during what was only a quote, and requests 12 and 13 are listed out of order because they share a request date.

## Suggested improvements
1. **Validate and fix dates and stock in the tools**: normalise `as_of_date` inside every tool and have the orchestrator pass the request date programmatically instead of through LLM text. This removes the false "out of stock / $0 cash" answers.
2. **Never expose internal finances**: map internal failure reasons (e.g. insufficient cash) to a customer-safe wording such as "currently unavailable for that date", and add an output check that strips internal figures.
3. **Structured request parsing**: have the orchestrator emit a validated JSON order (items, units, deadline, quote-only vs. order) to cut LLM unit-conversion errors (reams/boxes) and make sure confirmed orders always reach the ordering agent.
4. **Smarter reorder policy**: use sales velocity from `generate_financial_report` to set dynamic reorder points and batch restocks to hit cheaper lead-time tiers.
5. **Margin-aware discounting and partial fulfilment**: cap discounts using cost data, and ship the in-stock part of an order when other lines are unavailable.
