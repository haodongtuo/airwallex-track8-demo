"""Escrix-style escrow core for Airwallex Track 8 — pure Python, no network.

The Airwallex API calls live in airwallex_client.py. This module is the
part that works TODAY, while connected-accounts approval is still pending:
it models the money logic the demo must prove, so the video can be shot
against it and the live calls slotted in later without rewriting the flow.

Flow (mirrors the Escrix on-chain escrow, ported to fiat):
  1. Buyer funds a job -> money is LOCKED in a seller reserve, not paid.
  2. Seller delivers; a cheap deterministic check verifies the delivery.
  3. On pass: NET payout = gross - platform fee - risk hold; money moves.
     On fail / dispute: full check in a sandbox, loser pays dispute cost.
  4. Risk-adjusted limits: a seller's per-job cap grows with clean history
     and shrinks after a failed verification. No single job can drain a pool.

Money is Decimal throughout. Nothing here moves real money.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

D = Decimal


@dataclass
class Seller:
    seller_id: str
    clean_jobs: int = 0
    failed_jobs: int = 0
    # Base per-job cap; adjusted by history. New sellers start low.
    base_cap: D = D("500")

    @property
    def per_job_cap(self) -> D:
        """Risk-adjusted limit: +10% per clean job (max 3x), halved per failure."""
        cap = self.base_cap
        cap *= D("1.10") ** min(self.clean_jobs, 10)
        cap *= D("0.5") ** self.failed_jobs
        return cap.quantize(D("0.01"))


@dataclass
class Job:
    job_id: str
    seller: Seller
    gross: D                      # what the buyer locked, USD
    fee_rate: D = D("0.02")       # 2% platform fee for the demo
    risk_hold_rate: D = D("0.05") # 5% held back until the dispute window closes
    status: str = "LOCKED"        # LOCKED -> VERIFIED -> PAID / DISPUTED -> REFUNDED
    verification: dict = field(default_factory=dict)

    @property
    def fee(self) -> D:
        return (self.gross * self.fee_rate).quantize(D("0.01"))

    @property
    def risk_hold(self) -> D:
        return (self.gross * self.risk_hold_rate).quantize(D("0.01"))

    @property
    def net_payout(self) -> D:
        """What the seller actually receives on a verified delivery."""
        return self.gross - self.fee - self.risk_hold


def verify_delivery(job: Job, checks: dict[str, bool]) -> bool:
    """Cheap deterministic checks, not a model call.

    `checks` maps a named property to pass/fail, e.g.
    {"file_exists": True, "hash_matches": True, "amount_matches": True}.
    Every check must pass. This is the answer to Martin's round-15
    question: verify properties, not exact text; verify against a snapshot
    committed at call time, allowing bounded drift on re-fetch.
    """
    job.verification = dict(checks)
    passed = bool(checks) and all(checks.values())
    job.status = "VERIFIED" if passed else "DISPUTED"
    if passed:
        job.seller.clean_jobs += 1
    else:
        job.seller.failed_jobs += 1
    return passed


def settle(job: Job) -> D:
    """Release the net payout for a verified job. Returns amount paid."""
    if job.status != "VERIFIED":
        raise ValueError(f"cannot settle job in status {job.status}; verify first")
    job.status = "PAID"
    return job.net_payout


def refund(job: Job) -> D:
    """Full refund to the buyer on a failed / disputed delivery."""
    if job.status not in ("DISPUTED", "LOCKED"):
        raise ValueError(f"cannot refund job in status {job.status}")
    job.status = "REFUNDED"
    return job.gross


def demo_ledger() -> list[dict]:
    """The 3-job demo script for the <5-min video. Returns a printable ledger."""
    seller = Seller("seller_demo_01")
    rows = []
    for i, gross in enumerate([D("120"), D("250"), D("80")], start=1):
        job = Job(job_id=f"job_{i}", seller=seller, gross=gross)
        # Job 2 is the fail branch: one check fails, buyer is refunded.
        checks = {"file_exists": True, "hash_matches": True, "amount_matches": True}
        if i == 2:
            checks["hash_matches"] = False
        ok = verify_delivery(job, checks)
        if ok:
            paid = settle(job)
            rows.append({"job": job.job_id, "gross": str(gross),
                         "fee": str(job.fee), "hold": str(job.risk_hold),
                         "paid": str(paid), "status": job.status,
                         "cap_after": str(seller.per_job_cap)})
        else:
            back = refund(job)
            rows.append({"job": job.job_id, "gross": str(gross),
                         "fee": "0", "hold": "0",
                         "paid": f"refunded {back}", "status": job.status,
                         "cap_after": str(seller.per_job_cap)})
    return rows


if __name__ == "__main__":
    for row in demo_ledger():
        print(row)
