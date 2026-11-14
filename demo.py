"""Run the Track 8 demo end-to-end (offline escrow + live sandbox check).

Usage (from this folder):
    cp .env.example .env        # then put your API key in .env (never commit it)
    python3 demo.py             # escrow ledger first, sandbox check second
    python3 demo.py --offline   # escrow ledger only, no network

What the <5-min video shows, in order:
  1. Buyer locks $120 / $250 / $80 for three jobs (reserve, not payment).
  2. Deterministic checks verify each delivery (job 2 fails on hash mismatch).
  3. Verified jobs pay NET (gross - 2% fee - 5% risk hold); failed job refunds
     in full. Seller's per-job cap moves with history (risk-adjusted limits).
  4. Live sandbox: login + wallet balances prove the same account the
     approval request was filed under (acct_6nTcO1PLNw2O9S1QTrFzpQ) is real,
     and the connected-accounts probe reports whether approval has landed.
"""
from __future__ import annotations

import sys

from escrow import demo_ledger


def main() -> None:
    print("== Escrow ledger (offline, works today) ==")
    for row in demo_ledger():
        print(row)
    if "--offline" in sys.argv:
        return
    print("\n== Live sandbox check ==")
    try:
        import airwallex_client as aw
    except ImportError as e:
        print("cannot import airwallex_client:", e)
        return
    try:
        token = aw.login()
    except Exception as e:
        print("login failed (check .env — Client ID + API key):", e)
        print("Offline ledger above is still the demo. Fix .env and re-run.")
        return
    print("login OK")
    status, info = aw.wallet_info(token)
    print("wallet_info status:", status)
    print(info if isinstance(info, dict) else str(info)[:500])
    status, body = aw.try_create_connected_account(token)
    if status in (200, 201):
        print("CONNECTED ACCOUNTS ENABLED — approval landed, transfers are unblocked.")
    else:
        print(f"connected-accounts probe: HTTP {status} — approval NOT landed yet.")
        print("Keep building on the offline ledger + wallet_info; re-run this")
        print("after the Slack reply. Do not call create_transfer until then.")
        print(str(body)[:400])


if __name__ == "__main__":
    main()
