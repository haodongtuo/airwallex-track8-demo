"""Minimal Airwallex sandbox client — stdlib only (urllib), no pip installs.

Auth (verified against Airwallex docs, 2026-11-09):
  POST https://api.sandbox.airwallex.com/api/v1/authentication/login
    headers: x-client-id, x-api-key  -> returns {"token": ...}, valid 30 min.
  Every later call: Authorization: Bearer <token>.

Endpoints used (all sandbox):
  GET  /api/v1/account/wallet_info   — balances / account number (works NOW,
                                        no connected-accounts approval needed)
  POST /api/v1/accounts/create       — connected account. EXPECTED to fail
                                        with 400 until the team enables
                                        connected accounts + platform payments.
                                        That 400 IS the status check.
  POST /api/v1/transfers/create      — payout to a beneficiary (needs the
                                        approval above + a beneficiary; the
                                        function is ready, do not call it
                                        until the approval lands)
  POST /api/v1/beneficiaries/create  — save a beneficiary first, then pay by
                                        beneficiary_id.

Secrets: read AIRWALLEX_CLIENT_ID / AIRWALLEX_API_KEY from the environment
or a local .env file (see .env.example). NEVER commit .env, never paste the
API key into Slack / a repo / a chat screenshot.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

BASE = "https://api.sandbox.airwallex.com/api/v1"


def _env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value and os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            line = line.strip()
            if line.startswith(name + "="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not value:
        raise RuntimeError(f"missing {name} — copy .env.example to .env and fill it in")
    return value


def login() -> str:
    """Return a bearer token (valid 30 minutes)."""
    req = urllib.request.Request(
        f"{BASE}/authentication/login",
        method="POST",
        headers={
            "x-client-id": _env("AIRWALLEX_CLIENT_ID"),
            "x-api-key": _env("AIRWALLEX_API_KEY"),
            "Content-Type": "application/json",
        },
        data=b"{}",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["token"]


def _call(token: str, method: str, path: str, body: dict | None = None,
          extra_headers: dict | None = None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, {"error": e.read().decode(errors="replace")}


def wallet_info(token: str):
    """Balances etc. for the platform's own sandbox account. Works today."""
    return _call(token, "GET", "/account/wallet_info")


def try_create_connected_account(token: str):
    """Probe: returns (status, body). 200/201 means the approval HAS landed
    (a test connected account is created, status CREATED). 400 'cannot
    onboard business accounts' means it has NOT landed yet. Body follows
    the Airwallex quickstart (individual, minimal fields)."""
    return _call(token, "POST", "/accounts/create", {
        "account_details": {
            "legal_entity_type": "INDIVIDUAL",
            "individual_details": {
                "residential_address": {"country_code": "US"},
            },
        },
        "customer_agreements": {
            "agreed_to_data_usage": True,
            "agreed_to_terms_and_conditions": True,
        },
        "primary_contact": {"email": "demo@example.com"},
    })


def create_transfer(token: str, request_id: str, beneficiary_id: str,
                    amount: str, currency: str = "USD"):
    """Create a payout transfer. Call ONLY after connected-accounts approval.
    request_id must be unique within the past 7 days (Airwallex dedupes)."""
    return _call(token, "POST", "/transfers/create", {
        "request_id": request_id,
        "beneficiary_id": beneficiary_id,
        "transfer_amount": amount,
        "transfer_currency": currency,
        "transfer_method": "LOCAL",
    })


if __name__ == "__main__":
    token = login()
    print("login OK, token length:", len(token))
    status, info = wallet_info(token)
    print("wallet_info:", status)
    print(json.dumps(info, indent=2)[:1500])
    status, body = try_create_connected_account(token)
    print("connected-accounts probe:", status)
    print(json.dumps(body, indent=2)[:800])
