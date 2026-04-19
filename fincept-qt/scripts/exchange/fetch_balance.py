"""
Fetch account balance (requires API credentials via stdin).

Usage: echo '{"api_key":"...","secret":"..."}' | python fetch_balance.py <exchange_id>
Example: echo '{"api_key":"abc","secret":"xyz"}' | python fetch_balance.py binance

Output JSON:
{
  "success": true,
  "data": {
    "exchange": "binance",
    "balances": [
      {"currency": "BTC", "free": 0.5, "used": 0.1, "total": 0.6},
      {"currency": "USDT", "free": 10000.0, "used": 0.0, "total": 10000.0}
    ],
    "timestamp": 1773466621013
  }
}
"""

import sys
from exchange_client import (
    make_exchange,
    output_success,
    output_error,
    parse_credentials_from_stdin,
    run_with_error_handling,
)


def safe_float(x):
    try:
        return float(x or 0)
    except Exception:
        return 0.0


@run_with_error_handling
def main():
    # ---- ARG CHECK ----
    if len(sys.argv) < 2:
        output_error("Usage: fetch_balance.py <exchange_id>", "INVALID_ARGS")

    exchange_id = sys.argv[1]

    # ---- READ CREDS ----
    credentials = parse_credentials_from_stdin()

    if not credentials.get("api_key") or not credentials.get("secret"):
        output_error("API key and secret required.", "AUTH_ERROR")

    # ---- CREATE EXCHANGE ----
    exchange = make_exchange(exchange_id, credentials)

    # ---- FETCH BALANCE ----
    balance = exchange.fetch_balance()

    if not isinstance(balance, dict):
        output_error("Invalid balance response from exchange.", "EXCHANGE_ERROR")

    # ---- SAFE EXTRACTION ----
    totals = balance.get("total", {}) or {}
    frees = balance.get("free", {}) or {}
    useds = balance.get("used", {}) or {}

    if not isinstance(totals, dict):
        output_error("Malformed balance structure.", "EXCHANGE_ERROR")

    # ---- FILTER NON-ZERO ----
    balances = []

    for currency, total in totals.items():
        total_val = safe_float(total)

        if total_val > 0:
            balances.append({
                "currency": currency,
                "free": safe_float(frees.get(currency)),
                "used": safe_float(useds.get(currency)),
                "total": total_val,
            })

    # ---- SORT (HIGH → LOW) ----
    balances.sort(key=lambda x: x["total"], reverse=True)

    # ---- OUTPUT ----
    output_success({
        "exchange": exchange_id,
        "balances": balances,
        "timestamp": balance.get("timestamp"),
    })


if __name__ == "__main__":
    main()
